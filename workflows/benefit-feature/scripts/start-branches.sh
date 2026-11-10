#!/usr/bin/env bash
# Create (or switch to) the feature branch in each repo in scope.json (plan-gate has checked it).
# Usage: start-branches.sh <feature_dir>
# Only acts on a clean clone that is on main (or already on the feature branch); anything else stops the run.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
dir="${1:?feature dir}"; scope="$root/$dir/scope.json"; branch="feature/${dir##*/}"
[ -f "$scope" ] || { echo "$scope not found" >&2; exit 1; }
repos="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1])).get("repos", [])))' "$scope")"
[ -n "$repos" ] || { echo "scope.json names no repo" >&2; exit 1; }
for r in $repos; do
  d="$root/repos/$r"
  git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || { echo "repos/$r is not cloned (use the clone-repo skill)" >&2; exit 1; }
  cur="$(git -C "$d" symbolic-ref --short -q HEAD || echo detached)"
  if [ "$cur" = "$branch" ]; then echo "repos/$r: already on $branch"; continue; fi
  [ -z "$(git -C "$d" status --porcelain)" ] || { echo "repos/$r has uncommitted changes on $cur; commit or stash them first" >&2; exit 1; }
  git -C "$d" fetch -q origin
  if git -C "$d" show-ref -q --verify "refs/heads/$branch"; then
    git -C "$d" switch -q "$branch"; echo "repos/$r: switched to existing $branch"
  else
    [ "$cur" = "main" ] || [ "$cur" = "detached" ] || { echo "repos/$r is on '$cur'; switch to main first" >&2; exit 1; }
    git -C "$d" switch -q -c "$branch" origin/main; echo "repos/$r: created $branch from origin/main"
  fi
done
