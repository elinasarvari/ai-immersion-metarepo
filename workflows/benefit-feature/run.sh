#!/usr/bin/env bash
# One entry point for the benefit-feature workflow: checks the machine, prepares the repos, gives every
# unattended `claude -p` step its permissions, then starts, resumes, shows or watches a run.
#
#   workflows/benefit-feature/run.sh start  <feature> [pr_mode] [-i key=value ...]   e.g. start 001 ask
#   workflows/benefit-feature/run.sh resume [run-id] [-i key=value ...]              (default: latest run)
#   workflows/benefit-feature/run.sh status [run-id]
#   workflows/benefit-feature/run.sh watch  [run-id]                                 live progress view
#   workflows/benefit-feature/run.sh check                                           preflight only
#
# Why the permissions are passed explicitly: Claude Code applies a project's .claude/settings.json only after
# someone trusts the folder interactively. Passing the same file with --settings works without that, so a fresh
# clone runs unattended the same way on every machine.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$ROOT"
WF="workflows/benefit-feature/workflow.yml"
SETTINGS="$ROOT/.claude/settings.json"
RUNS="$ROOT/.specify/workflows/runs"

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
die() { red "✗ $*"; exit 1; }

latest_run() { ls -t "$RUNS" 2>/dev/null | head -1; }

check_tools() {
  local missing=""
  for t in specify claude git gh uv pnpm make python3; do
    command -v "$t" >/dev/null 2>&1 || missing="$missing $t"
  done
  [ -z "$missing" ] || die "missing tools:$missing"
  python3 -m json.tool "$SETTINGS" >/dev/null 2>&1 || die "$SETTINGS is missing or not valid JSON (it holds the agents' permissions)"
  note "tools: specify, claude, git, gh, uv, pnpm, make, python3 ✓  permissions: .claude/settings.json ✓"
}

check_gh() {  # only needed when the run may push
  gh auth status >/dev/null 2>&1 || die "gh is not logged in (gh auth login); needed to open PRs. Use pr_mode none to skip."
  note "gh: logged in ✓"
}

# Put each clone on an up-to-date main, or on this feature's branch when resuming it. Switches only what is
# safe to switch (clean, nothing unpushed); anything else stops with the reason.
prepare_repos() {
  local feature_branch="$1" dry="${2:-}" r d cur ahead behind
  for r in benefit-be benefit-fe; do
    d="repos/$r"
    git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || die "$d is not cloned (skills/clone-repo/clone-repo.sh <url>)"
    git -C "$d" fetch -q origin || die "$d: git fetch failed"
    if [ -n "$(git -C "$d" status --porcelain)" ]; then
      git -C "$d" status --short | head -10
      die "$d has uncommitted changes; commit or stash them (to continue an earlier run of this feature: run.sh resume)"
    fi
    cur="$(git -C "$d" symbolic-ref --short -q HEAD || echo detached)"
    if [ "$cur" = "$feature_branch" ]; then note "$r: on $cur (this feature) ✓"; continue; fi
    if [ -n "$dry" ]; then
      behind="$(git -C "$d" rev-list --count HEAD..origin/main)"
      note "$r: on $cur, clean, $behind behind origin/main (start will switch to main and fast-forward if safe)"; continue
    fi
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

export_permissions() {
  export SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS="--settings $SETTINGS"
}

pr_mode_of() {  # the pr_mode a run was started with
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["inputs"].get("pr_mode","draft"))' "$RUNS/$1/inputs.json" 2>/dev/null || echo draft
}

cmd="${1:-}"; shift || true
case "$cmd" in
  check)
    echo "Preflight (changes nothing)"; check_tools; check_gh; prepare_repos "__none__" dry; green "✓ ready" ;;
  start)
    feature="${1:?usage: run.sh start <feature> [pr_mode] [-i key=value ...]}"; shift
    pr_mode="draft"
    if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then pr_mode="$1"; shift; fi
    echo "Preflight"
    check_tools
    [ "$pr_mode" = "none" ] || check_gh
    folder="$(python3 - "$feature" <<'EOF'
import sys
from pathlib import Path
f = sys.argv[1]
c = [Path(f)] if "/" in f else ([Path("specs") / f] if (Path("specs") / f).is_dir() else sorted(Path("specs").glob(f + "-*")))
c = [p for p in c if (p / "spec.md").exists()]
print(c[0].name if len(c) == 1 else "")
EOF
)"
    [ -n "$folder" ] || die "no single spec folder matches '$feature' under specs/"
    prepare_repos "feature/$folder"
    export_permissions
    green "✓ ready: $folder, pr_mode=$pr_mode"
    note "watch it in another terminal: workflows/benefit-feature/run.sh watch"
    echo
    exec specify workflow run "$WF" -i feature="$folder" -i pr_mode="$pr_mode" "$@" ;;
  resume)
    id="${1:-}"; if [ -n "$id" ] && [ "${id#-}" = "$id" ]; then shift; else id="$(latest_run)"; fi
    [ -n "$id" ] || die "no runs yet; start one with: run.sh start <feature>"
    echo "Preflight for run $id"
    check_tools
    [ "$(pr_mode_of "$id")" = "none" ] || check_gh
    export_permissions
    green "✓ resuming $id"
    note "watch it in another terminal: workflows/benefit-feature/run.sh watch $id"
    echo
    exec specify workflow resume "$id" "$@" ;;
  status)
    id="${1:-$(latest_run)}"; [ -n "$id" ] || die "no runs yet"
    exec specify workflow status "$id" < /dev/null ;;
  watch)
    exec python3 workflows/benefit-feature/scripts/watch.py "$@" ;;
  *)
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
