#!/usr/bin/env bash
# Report how a repo's current branch relates to its remote default branch. Read-only.
#
# Usage: branch-status.sh <repo-name>      (a clone at repos/<repo-name>)
#
# Prints KEY=value lines, then a one-line summary:
#   REPO, BRANCH, BASE (origin/<default>), MERGE_BASE, AHEAD, BEHIND, UNCOMMITTED,
#   MERGE (clean | conflict | unknown), CONFLICT_FILES (comma-separated), DIFF (the range to review)
# Exit codes: 0 ok, 1 would conflict with the base, 2 usage/setup error.
set -uo pipefail

name="${1:-}"; [ -n "$name" ] || { echo "usage: $0 <repo-name>" >&2; exit 2; }
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
dir="$root/repos/$name"
git -C "$dir" rev-parse --git-dir >/dev/null 2>&1 || { echo "repos/$name is not a git repo" >&2; exit 2; }

# 1. Fetch, so the comparison is against the real current remote, not a stale copy.
git -C "$dir" fetch -q origin || { echo "fetch failed for repos/$name (auth/network?)" >&2; exit 2; }

# 2. Resolve the actual default branch instead of assuming main.
git -C "$dir" remote set-head origin --auto >/dev/null 2>&1 || true
base="$(git -C "$dir" symbolic-ref --short -q refs/remotes/origin/HEAD || true)"
if [ -z "$base" ]; then
  for b in main master; do git -C "$dir" show-ref -q --verify "refs/remotes/origin/$b" && { base="origin/$b"; break; }; done
fi
[ -n "$base" ] || { echo "can't determine the default branch of repos/$name" >&2; exit 2; }

branch="$(git -C "$dir" symbolic-ref --short -q HEAD || echo "(detached)")"
mb="$(git -C "$dir" merge-base "$base" HEAD)"
read -r behind ahead < <(git -C "$dir" rev-list --left-right --count "$base...HEAD")
uncommitted="$(git -C "$dir" status --porcelain | wc -l | tr -d ' ')"

# 3. Would the branch merge cleanly into the current base? (in-memory, touches nothing)
merge="clean" files=""
if [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
  if out="$(git -C "$dir" merge-tree --write-tree --name-only --no-messages "$base" HEAD 2>/dev/null)"; then
    merge="clean"
  elif [ $? -eq 1 ]; then
    merge="conflict"; files="$(printf '%s\n' "$out" | tail -n +2 | grep -v '^$' | paste -sd, -)"
  else
    merge="unknown"
  fi
fi

cat <<OUT
REPO=$name
BRANCH=$branch
BASE=$base
MERGE_BASE=${mb:0:12}
AHEAD=$ahead
BEHIND=$behind
UNCOMMITTED=$uncommitted
MERGE=$merge
CONFLICT_FILES=$files
DIFF=$base...HEAD
OUT

summary="repos/$name: $branch is $ahead ahead, $behind behind $base"
[ "$uncommitted" -eq 0 ] || summary="$summary, $uncommitted uncommitted file(s)"
case "$merge" in
  conflict) echo "SUMMARY: $summary; WOULD CONFLICT in: $files"; exit 1 ;;
  unknown)  echo "SUMMARY: $summary; merge check failed" ;;
  *)        echo "SUMMARY: $summary; merges cleanly" ;;
esac
