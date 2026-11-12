#!/usr/bin/env bash
# Check and sync the plain git clones under repos/ to the latest default branch (usually main).
#
# Usage: sync-repos.sh [--check] [repo-name ...]
#   (no flags)  validate repos/, fast-forward clean ones to origin/<default>
#   --check     validate and report only; change nothing; exit 1 if anything is wrong or behind
#
# Safety: a clone is only moved when its working tree is clean and it is on the default
# branch (or detached at a commit already contained in it). Feature branches, local changes and
# unpushed commits are reported and left alone. Never force, never reset.
# repos/ holds plain clones (see clone-repo skill) - nothing here is tracked by the metarepo. Inside a feature
# worktree (workflows/benefit-feature/run.sh) they are git worktrees of those clones, on the feature branch.
set -uo pipefail

check="" only=()
for a in "$@"; do
  case "$a" in
    --check) check=1 ;;
    -*) echo "unknown option: $a" >&2; exit 2 ;;
    *) only+=("repos/$a") ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
cd "$root"

problems=0 behind=0 updated=() skipped=()
ok()   { printf '  ✓ %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*"; }
bad()  { printf '  ✗ %s\n' "$*"; problems=$((problems+1)); }

echo "== Validating repos/"
paths=()
if [ -d repos ]; then
  for d in repos/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"
    [ -e "$d/.gitkeep" ] && [ "$(ls -A "$d")" = ".gitkeep" ] && continue
    if [ ! -e "$d/.git" ]; then bad "$d: not a git repo"; continue; fi
    if [ -f "$d/.git" ]; then
      # A feature worktree (workflows/benefit-feature/run.sh) has repos/<name> as git worktrees of the main
      # clones: fine, and on a feature branch, so the loop below leaves them alone.
      if grep -q '^gitdir: .*/worktrees/' "$d/.git"; then paths+=("$d"); continue; fi
      bad "$d: looks like a submodule gitlink, expected a plain clone (run: skills/clone-repo/clone-repo.sh to recreate)"; continue
    fi
    paths+=("$d")
  done
fi
[ ${#paths[@]} -gt 0 ] || { echo "No clones found under repos/. Add one with skills/clone-repo/clone-repo.sh"; exit 0; }

[ ${#only[@]} -eq 0 ] || paths=("${only[@]}")

echo "== Syncing repos"
for p in "${paths[@]}"; do
  echo "-- $p"
  if ! git -C "$p" fetch -q origin; then bad "fetch failed (auth/network?)"; continue; fi
  [ -n "$check" ] || git -C "$p" worktree prune  # forget worktrees whose folder was deleted by hand
  git -C "$p" remote set-head origin --auto >/dev/null 2>&1 || true
  def="$(git -C "$p" symbolic-ref --short -q refs/remotes/origin/HEAD || echo origin/main)"; def="${def#origin/}"
  target="origin/$def"
  branch="$(git -C "$p" symbolic-ref --short -q HEAD || true)"
  head="$(git -C "$p" rev-parse HEAD)"; tip="$(git -C "$p" rev-parse "$target")"

  if [ -n "$(git -C "$p" status --porcelain)" ]; then
    warn "has uncommitted changes on ${branch:-detached HEAD}; left alone"; skipped+=("$p"); continue
  fi
  if [ -n "$branch" ] && [ "$branch" != "$def" ]; then
    n="$(git -C "$p" rev-list --count "$target..$branch")"
    warn "on feature branch '$branch' ($n commit(s) not in $def); left alone"; skipped+=("$p"); continue
  fi
  if [ "$head" = "$tip" ]; then ok "up to date with $target (${tip:0:7})"; continue; fi
  if ! git -C "$p" merge-base --is-ancestor "$head" "$tip"; then
    warn "HEAD ${head:0:7} has commits not in $target; left alone"; skipped+=("$p"); continue
  fi
  n="$(git -C "$p" rev-list --count "$head..$tip")"
  if [ -n "$check" ]; then warn "$n commit(s) behind $target"; behind=$((behind+1)); continue; fi
  if [ -n "$branch" ]; then git -C "$p" merge -q --ff-only "$target"
  elif git -C "$p" show-ref --verify -q "refs/heads/$def"; then
    git -C "$p" switch -q "$def" && git -C "$p" merge -q --ff-only "$target" \
      || { warn "local '$def' can't fast-forward; left detached"; skipped+=("$p"); continue; }
  else git -C "$p" switch -q -c "$def" --track "$target"; fi
  ok "fast-forwarded $n commit(s) to $target (${tip:0:7})"; updated+=("$p")
done

echo "== Summary: ${#updated[@]} updated, ${#skipped[@]} left alone, $behind behind, $problems problem(s)"
[ "$problems" -eq 0 ] && { [ -z "$check" ] || [ "$behind" -eq 0 ]; }
