#!/usr/bin/env bash
# Create (or switch to) the feature branch in each repo that plan.md targets.
# Usage: start-branches.sh <feature_dir>
# Only acts on a clean clone that is on main (or already on the feature branch); anything else stops the run.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
dir="${1:?feature dir}"; plan="$root/$dir/plan.md"; branch="feature/${dir##*/}"
[ -f "$plan" ] || { echo "$plan not found" >&2; exit 1; }
repos="$(grep -oE 'repos/benefit-(be|fe)' "$plan" | sort -u | sed 's#repos/##')"
[ -n "$repos" ] || { echo "plan.md names no target repo (repos/benefit-be or repos/benefit-fe)" >&2; exit 1; }
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
