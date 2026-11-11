#!/usr/bin/env bash
# One entry point for the benefit-feature workflow: checks the machine, gives each feature its own worktree,
# gives every unattended `claude -p` step its permissions, then starts, resumes, shows or watches a run.
#
#   workflows/benefit-feature/run.sh start   <feature> [-i key=value ...]            e.g. start 001
#                     one way: agents decide, then draft PRs, ready for review once CI is green
#   workflows/benefit-feature/run.sh start   --in-place <feature> ...               old way: in this checkout
#   workflows/benefit-feature/run.sh prepare <feature>                              only create the worktree
#   workflows/benefit-feature/run.sh resume  [run-id|NNN] [-i key=value ...]        (default: latest run)
#   workflows/benefit-feature/run.sh status  [run-id|NNN]
#   workflows/benefit-feature/run.sh watch   [run-id|NNN] [--once]                  live progress view
#   workflows/benefit-feature/run.sh worktrees                                      list feature worktrees
#   workflows/benefit-feature/run.sh cleanup <feature> [--yes]                      remove a feature's worktrees
#   workflows/benefit-feature/run.sh check                                          preflight only
#
# Worktrees: each feature runs in <metarepo>.worktrees/<NNN-name>/ (override with WF_WORKTREES), a git worktree
# of the metarepo on feature/<NNN-name> whose repos/<name> are git worktrees of the main clones on the same
# branch. Paths inside it are the same as here, so features run side by side and the main checkout and clones
# stay free. It is a sibling folder, not a subfolder, so agents don't also load this checkout's CLAUDE.md.
#
# Why the permissions are passed explicitly: Claude Code applies a project's .claude/settings.json only after
# someone trusts the folder interactively. Passing the same file with --settings works without that, so a fresh
# clone runs unattended the same way on every machine.
set -euo pipefail
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"   # the checkout this script is in
# The main checkout, even when this script runs from inside a feature worktree.
MAIN="$(cd "$(dirname "$(git -C "$SELF" rev-parse --path-format=absolute --git-common-dir)")" && pwd -P)"
WT_HOME="${WF_WORKTREES:-$(dirname "$MAIN")/$(basename "$MAIN").worktrees}"
WF="workflows/benefit-feature/workflow.yml"
REPOS="benefit-be benefit-fe"
# Paths whose uncommitted changes a worktree run doesn't see (it runs the committed agents, rules and workflow).
TOOLING="workflows agents skills project-rules .claude .specify/memory .specify/templates .specify/scripts"
cd "$MAIN"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
die() { red "✗ $*"; exit 1; }

check_tools() {  # $1 = the settings file the run will use
  local settings="$1" missing="" t missing_rules
  for t in specify claude git gh uv pnpm make python3; do
    command -v "$t" >/dev/null 2>&1 || missing="$missing $t"
  done
  [ -z "$missing" ] || die "missing tools:$missing"
  python3 -m json.tool "$settings" >/dev/null 2>&1 || die "$settings is missing or not valid JSON (it holds the agents' permissions)"
  missing_rules="$(python3 "$SELF/workflows/benefit-feature/scripts/check_permissions.py" "$settings")" \
    || die "the agents' permissions in $settings lack: $missing_rules"
  note "tools: specify, claude, git, gh, uv, pnpm, make, python3 ✓  permissions: .claude/settings.json ✓"
}

check_ports() {  # information only: the e2e job runs on free ports of its own (benefit-be's `make verify-stack`)
  local busy
  busy="$(python3 "$SELF/workflows/benefit-feature/scripts/wf.py" ports \
    | python3 -c 'import json,sys; print("\n".join("port %s: %s" % (b["port"], b["holder"]) for b in json.load(sys.stdin)["busy"]))' 2>/dev/null || true)"
  if [ -n "$busy" ]; then
    note "default stack ports in use (fine: e2e runs on free ports of its own, and nothing else is touched):"
    printf '%s\n' "$busy" | sed 's/^/      /'
    note "  an older branch without 'make verify-stack' still skips e2e locally while these are taken"
  else
    note "stack ports free ✓ (e2e runs on free ports of its own either way)"
  fi
}

check_gh() {  # every run ends by pushing and opening PRs
  gh auth status >/dev/null 2>&1 || die "gh is not logged in (gh auth login); needed to open PRs."
  note "gh: logged in ✓"
}

check_clones() {  # the main clones exist and can fetch (worktrees share their refs, so one fetch serves all)
  local r d
  for r in $REPOS; do
    d="$MAIN/repos/$r"
    git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || die "repos/$r is not cloned (skills/clone-repo/clone-repo.sh <url>)"
    git -C "$d" fetch -q origin || die "repos/$r: git fetch failed"
  done
  note "clones: $REPOS fetched ✓"
}

feature_folder() {  # the one specs/<NNN-name> folder matching $1, from the main checkout
  python3 - "$1" <<'EOF'
import sys
from pathlib import Path
f = sys.argv[1]
c = [Path(f)] if "/" in f else ([Path("specs") / f] if (Path("specs") / f).is_dir() else sorted(Path("specs").glob(f + "-*")))
c = [p for p in c if (p / "spec.md").exists()]
print(c[0].name if len(c) == 1 else "")
EOF
}

# ── In-place mode (the old way): put each clone of this checkout on an up-to-date main, or on this feature's
#    branch when it is already there. Switches only what is safe to switch (clean, nothing unpushed).
prepare_repos_in_place() {
  local feature_branch="$1" r d cur ahead
  for r in $REPOS; do
    d="repos/$r"
    if [ -n "$(git -C "$d" status --porcelain)" ]; then
      git -C "$d" status --short | head -10
      die "$d has uncommitted changes; commit or stash them (to continue an earlier run of this feature: run.sh resume)"
    fi
    cur="$(git -C "$d" symbolic-ref --short -q HEAD || echo detached)"
    if [ "$cur" = "$feature_branch" ]; then note "$r: on $cur (this feature) ✓"; continue; fi
    if [ "$cur" != "main" ]; then
      ahead="$(git -C "$d" rev-list --count origin/main..HEAD)"
      [ "$ahead" = "0" ] || die "$d is on '$cur' with $ahead commit(s) not on origin/main; push or switch it yourself"
      git -C "$d" switch -q main
      note "$r: switched from $cur (nothing unpushed) to main"
    fi
    git -C "$d" merge -q --ff-only origin/main || die "$d: main can't fast-forward to origin/main"
    note "$r: main at $(git -C "$d" rev-parse --short HEAD) = origin/main ✓"
  done
}

# ── Worktrees ─────────────────────────────────────────────────────────────────────────────────────────────
install_deps() {  # $1 = worktree of a clone; only what is missing, so a reused worktree costs nothing
  local d="$1"
  if [ -f "$d/pyproject.toml" ] && [ ! -d "$d/.venv" ]; then
    (cd "$d" && uv sync --frozen -q) || die "$d: uv sync failed"
    note "  python deps installed (uv sync)"
  fi
  if [ -f "$d/package.json" ] && [ ! -d "$d/node_modules" ]; then
    (cd "$d" && pnpm install --frozen-lockfile --silent) || die "$d: pnpm install failed"
    note "  node deps installed (pnpm install)"
  fi
}

prepare_clone_worktree() {  # $1 repo, $2 metarepo worktree, $3 branch
  local r="$1" wt="$2" branch="$3" m="$MAIN/repos/$1" d="$2/repos/$1" cur f
  if [ -e "$d/.git" ]; then
    cur="$(git -C "$d" symbolic-ref --short -q HEAD || echo detached)"
    [ "$cur" = "$branch" ] || die "$d is on '$cur', expected $branch; switch it back, or remove the worktree (run.sh cleanup)"
    note "$r: worktree on $branch ✓"
  else
    # git checks a branch out in one place only: free it if the main clone still has it (the old in-place way).
    cur="$(git -C "$m" symbolic-ref --short -q HEAD || echo detached)"
    if [ "$cur" = "$branch" ]; then
      [ -z "$(git -C "$m" status --porcelain)" ] \
        || die "repos/$r is on $branch with uncommitted changes; commit or stash them there, then start again"
      if git -C "$m" show-ref -q --verify refs/heads/main; then git -C "$m" switch -q main
      else git -C "$m" switch -q --detach origin/main; fi
      note "$r: main clone moved off $branch (clean) so the worktree can take it"
    fi
    if git -C "$m" show-ref -q --verify "refs/heads/$branch"; then
      git -C "$m" worktree add -q "$d" "$branch" || die "repos/$r: can't check out $branch in a worktree (git worktree list)"
      note "$r: worktree on existing $branch"
    elif git -C "$m" show-ref -q --verify "refs/remotes/origin/$branch"; then
      git -C "$m" worktree add -q --track -b "$branch" "$d" "origin/$branch" || die "repos/$r: git worktree add failed"
      note "$r: worktree on $branch from origin/$branch"
    else
      git -C "$m" worktree add -q --no-track -b "$branch" "$d" origin/main || die "repos/$r: git worktree add failed"
      note "$r: worktree on new $branch from origin/main ($(git -C "$d" rev-parse --short HEAD))"
    fi
    for f in .env .env.local; do  # local, git-ignored settings the checks need
      [ -f "$m/$f" ] && [ ! -e "$d/$f" ] && cp "$m/$f" "$d/$f" && note "  copied $f from the main clone"
    done
  fi
  install_deps "$d"
}

prepare_worktree() {  # $1 = spec folder; sets WT
  local folder="$1" branch="feature/$1" fresh="" new_branch="" r dirty
  WT="$WT_HOME/$folder"
  if [ -e "$WT/.git" ]; then
    note "metarepo: reusing worktree $WT ($(git -C "$WT" symbolic-ref --short -q HEAD || echo detached))"
  else
    mkdir -p "$WT_HOME"
    if git show-ref -q --verify "refs/heads/$branch"; then
      git worktree add -q "$WT" "$branch" \
        || die "can't check out $branch in a worktree; if this checkout is on it, switch away or use: run.sh start --in-place"
    else
      git worktree add -q -b "$branch" "$WT" HEAD || die "git worktree add failed"
      new_branch=1
    fi
    fresh=1
    note "metarepo: worktree $WT on $branch ($(git -C "$WT" rev-parse --short HEAD))"
  fi
  # The spec usually exists only here so far: bring it along, once, before the run writes into the worktree.
  if [ -n "$fresh" ] && { [ ! -f "$WT/specs/$folder/spec.md" ] \
       || { [ -n "$new_branch" ] && [ -n "$(git status --porcelain -- "specs/$folder")" ]; }; }; then
    mkdir -p "$WT/specs/$folder"
    cp -R "specs/$folder/." "$WT/specs/$folder/"
    note "copied specs/$folder (with its uncommitted changes) into the worktree"
  fi
  dirty="$(git status --porcelain -- $TOOLING | head -5)"
  if [ -n "$dirty" ]; then
    yellow "  ! uncommitted changes here are not in the worktree; the run uses the committed version:"
    printf '%s\n' "$dirty" | sed 's/^/      /'
    note "  (commit them and start a new feature, or use: run.sh start --in-place)"
  fi
  for r in $REPOS; do prepare_clone_worktree "$r" "$WT" "$branch"; done
}

# ── Runs live in the checkout or worktree that started them ──────────────────────────────────────────────
run_dirs() {  # every run, newest first
  ls -td "$MAIN"/.specify/workflows/runs/*/ "$WT_HOME"/*/.specify/workflows/runs/*/ 2>/dev/null || true
}

find_run() {  # $1 = run id, NNN feature, or empty for the latest; sets RUN_ID and RUN_HOME
  local p=""
  if [ -z "${1:-}" ]; then p="$(run_dirs | head -1 || true)"
  elif [[ "$1" =~ ^[0-9]{3}$ ]]; then  # the feature's worktree runs, and in-place runs of it in this checkout
    p="$(python3 -c 'import glob, json, os, sys
n, main, wt = sys.argv[1:4]
runs = glob.glob(wt + "/" + n + "-*/.specify/workflows/runs/*/")
for d in glob.glob(main + "/.specify/workflows/runs/*/"):
    try:
        feature = json.load(open(d + "inputs.json"))["inputs"].get("feature", "")
    except (OSError, ValueError, KeyError):
        continue
    if feature.startswith(n):
        runs.append(d)
runs.sort(key=os.path.getmtime, reverse=True)
print(runs[0] if runs else "")' "$1" "$MAIN" "$WT_HOME")"
  else p="$(ls -d "$MAIN/.specify/workflows/runs/$1/" "$WT_HOME"/*/.specify/workflows/runs/"$1"/ 2>/dev/null | head -1 || true)"
  fi
  [ -n "$p" ] || die "no run found for '${1:-latest}'; start one with: run.sh start <feature>"
  p="${p%/}"; RUN_ID="${p##*/}"; RUN_HOME="${p%/.specify/workflows/runs/*}"
}

run_env() {  # $1 = where the run lives
  export SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS="--settings $1/.claude/settings.json"
  # One local mongod for every worktree (the Makefile would otherwise look for one per worktree, on the same port).
  [ "$1" = "$MAIN" ] || export MONGO_DIR="${MONGO_DIR:-$MAIN/repos/benefit-be/.data/mongo}"
}

free_ports() {  # $1 = where the run lives, $2 = feature folder: stop what the run left listening, whatever its outcome
  [ -n "${2:-}" ] && [ -d "$1/specs/$2" ] || return 0
  echo
  if (cd "$1" && python3 workflows/benefit-feature/scripts/wf.py ports-freed "specs/$2" > /dev/null); then
    note "ports: nothing this run started is still listening (specs/$2/review/ports.md)"
  else
    yellow "  ! one of this run's processes is still listening; see $1/specs/$2/review/ports.md"
  fi
  grep -q "^- warning" "$1/specs/$2/review/ports.md" 2>/dev/null \
    && note "ports held by processes this run didn't start are listed there (left alone)"
  return 0
}

run_engine() {  # $1 = where the run lives, $2 = feature folder, then the engine command; keeps its exit code
  local home="$1" folder="$2" code=0
  shift 2
  trap 'free_ports "$home" "$folder"; exit 130' INT TERM
  "$@" || code=$?
  trap - INT TERM
  free_ports "$home" "$folder"
  return "$code"
}

run_feature() {  # the feature folder a run was started for
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["inputs"].get("feature",""))' \
    "$RUN_HOME/.specify/workflows/runs/$RUN_ID/inputs.json" 2>/dev/null || true
}

cleanup() {  # $1 = feature, $2 = --yes
  local folder wt r d dirty="" ans
  folder="$(cd "$WT_HOME" 2>/dev/null && ls -d "$1" "$1"-* 2>/dev/null | head -1 || true)"
  [ -n "$folder" ] && [ -e "$WT_HOME/$folder/.git" ] || die "no worktree for '$1' in $WT_HOME (run.sh worktrees)"
  wt="$WT_HOME/$folder"
  for d in "$wt" "$wt/repos/benefit-be" "$wt/repos/benefit-fe"; do
    [ -e "$d/.git" ] || continue
    if [ -n "$(git -C "$d" status --porcelain)" ]; then
      red "  $d has uncommitted changes:"; git -C "$d" status --short | head -10 | sed 's/^/      /'; dirty=1
    fi
  done
  [ -z "$dirty" ] || die "nothing removed; commit (e.g. the spec artefacts on feature/$folder) or discard those changes first"
  echo "Removes $wt and its clone worktrees. Branches (feature/$folder) and their commits stay; run state and logs go."
  if [ "${2:-}" != "--yes" ]; then
    [ -t 0 ] || die "not a terminal: pass --yes once the user has confirmed"
    read -r -p "  remove? [y/N] " ans; [ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "cancelled"
  fi
  for r in $REPOS; do
    [ -e "$wt/repos/$r/.git" ] || continue
    git -C "$MAIN/repos/$r" worktree remove "$wt/repos/$r" || die "repos/$r: git worktree remove failed"
    note "$r: worktree removed"
  done
  git worktree remove "$wt" || die "git worktree remove $wt failed"
  git worktree prune
  green "✓ removed $wt (branches kept)"
}

list_worktrees() {
  local wt d any="" run label
  for wt in "$WT_HOME"/*/; do
    wt="${wt%/}"; [ -e "$wt/.git" ] || continue; any=1
    run="$(ls -td "$wt"/.specify/workflows/runs/*/ 2>/dev/null | head -1 || true)"; run="${run%/}"
    echo "${wt##*/}  (latest run: ${run##*/})"
    for d in "$wt" "$wt/repos/benefit-be" "$wt/repos/benefit-fe"; do
      [ -e "$d/.git" ] || continue
      label="${d#"$wt"}"; label="${label#/repos/}"
      note "$(printf '%-11s' "${label:-metarepo}") $(git -C "$d" symbolic-ref --short -q HEAD || echo detached), $(git -C "$d" status --porcelain | wc -l | tr -d ' ') changed file(s)"
    done
  done
  [ -n "$any" ] || echo "no feature worktrees in $WT_HOME"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  check)
    echo "Preflight (changes nothing)"; check_tools "$MAIN/.claude/settings.json"; check_gh; check_clones; check_ports
    note "feature worktrees: $WT_HOME"; green "✓ ready" ;;
  prepare|start)
    in_place=""; args=()
    for a in "$@"; do if [ "$a" = "--in-place" ]; then in_place=1; else args+=("$a"); fi; done
    set -- ${args[@]+"${args[@]}"}
    feature="${1:?usage: run.sh $cmd <feature> [-i key=value ...]}"; shift
    if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
      die "unexpected '$1': there are no modes any more (a run always decides, then opens draft PRs); usage: run.sh $cmd <feature> [-i key=value ...]"
    fi
    folder="$(feature_folder "$feature")"
    [ -n "$folder" ] || die "no single spec folder matches '$feature' under specs/"
    echo "Preflight"
    [ "$cmd" = "prepare" ] || check_gh
    check_clones
    if [ -n "$in_place" ]; then
      prepare_repos_in_place "feature/$folder"; home="$MAIN"
    else
      prepare_worktree "$folder"; home="$WT"
    fi
    [ "$cmd" = "prepare" ] || check_tools "$home/.claude/settings.json"  # the permissions this run will use
    [ "$cmd" = "prepare" ] || check_ports
    if [ "$cmd" = "prepare" ]; then green "✓ prepared $home"; exit 0; fi
    run_env "$home"
    green "✓ ready: $folder, in $home"
    note "watch it in another terminal: workflows/benefit-feature/run.sh watch ${folder%%-*}"
    echo
    cd "$home"
    code=0; run_engine "$home" "$folder" specify workflow run "$WF" -i feature="$folder" "$@" || code=$?
    exit "$code" ;;
  resume)
    id=""; if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then id="$1"; shift; fi
    find_run "$id"
    echo "Preflight for run $RUN_ID ($RUN_HOME)"
    check_tools "$RUN_HOME/.claude/settings.json"
    check_gh
    check_ports
    run_env "$RUN_HOME"
    green "✓ resuming $RUN_ID"
    note "watch it in another terminal: workflows/benefit-feature/run.sh watch $RUN_ID"
    echo
    cd "$RUN_HOME"
    code=0; run_engine "$RUN_HOME" "$(run_feature)" specify workflow resume "$RUN_ID" "$@" || code=$?
    exit "$code" ;;
  status)
    find_run "${1:-}"; cd "$RUN_HOME"
    exec specify workflow status "$RUN_ID" < /dev/null ;;
  watch)  # also notifies (macOS) when the run waits for you, fails or finishes
    id=""; if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then id="$1"; shift; fi
    find_run "$id"
    WF_ROOT="$RUN_HOME" exec python3 "$SELF/workflows/benefit-feature/scripts/watch.py" --notify "$RUN_ID" "$@" ;;
  worktrees)
    list_worktrees ;;
  cleanup)
    cleanup "${1:?usage: run.sh cleanup <feature> [--yes]}" "${2:-}" ;;
  *)
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
