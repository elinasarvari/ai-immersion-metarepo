#!/usr/bin/env bash
# Branch, commit, push and open a PR for changes inside a linked submodule (repos/<name>).
#
# Usage:
#   create-pr.sh <repo-name> --branch <branch> --message <commit-msg>
#                [--title <pr-title>] [--body-file <file>] [--base main] [--draft] [--no-pr]
#
# - Works only on submodules registered under repos/ in .gitmodules.
# - Pushes to that submodule's own `origin`, so code always lands in the right repository.
# - Never pushes to the base branch and never force-pushes.
set -euo pipefail

die() { echo "Error: $*" >&2; exit 1; }

name="${1:-}"; [ -n "$name" ] && [ "${name#-}" = "$name" ] || die "usage: $0 <repo-name> --branch <b> --message <m> [...]"
shift
branch="" message="" title="" body_file="" base="main" draft="" no_pr=""
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) branch="${2:-}"; shift 2 ;;
    --message|-m) message="${2:-}"; shift 2 ;;
    --title) title="${2:-}"; shift 2 ;;
    --body-file) body_file="${2:-}"; shift 2 ;;
    --base) base="${2:-}"; shift 2 ;;
    --draft) draft="--draft"; shift ;;
    --no-pr) no_pr=1; shift ;;
    *) die "unknown option: $1" ;;
  esac
done
[ -n "$branch" ] || die "--branch is required"
[ "$branch" != "$base" ] || die "branch must differ from base ($base)"
git check-ref-format --branch "$branch" >/dev/null 2>&1 || die "invalid branch name: $branch"
[ -z "$body_file" ] || [ -f "$body_file" ] || die "body file not found: $body_file"
case "$body_file" in ""|/*) ;; *) body_file="$PWD/$body_file" ;; esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
path="repos/$name"
git -C "$root" config -f "$root/.gitmodules" --get "submodule.$path.url" >/dev/null 2>&1 \
  || die "$path is not a registered submodule (add it with skills/clone-repo/clone-repo.sh)"
dir="$root/$path"
[ -e "$dir/.git" ] || die "$path is not initialised (run: git submodule update --init $path)"
cd "$dir"

remote_url="$(git remote get-url origin)"
echo "Repository: $path -> $remote_url"

git fetch origin "$base" --quiet || die "could not fetch origin/$base"

current="$(git symbolic-ref --short -q HEAD || true)"
if [ "$current" = "$branch" ]; then
  echo "Already on branch $branch"
elif git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch "$branch"        # carries uncommitted changes; fails safely on conflict
else
  [ -z "$current" ] || [ "$current" = "$base" ] \
    || die "on unrelated branch '$current'; switch back to $base or pass --branch $current"
  # Branch from the latest remote base; uncommitted work is carried over.
  # If HEAD is behind origin/$base and the changes conflict, git refuses and nothing is lost.
  git switch -c "$branch" "origin/$base" 2>/dev/null || git switch -c "$branch"
fi

if [ -n "$(git status --porcelain)" ]; then
  [ -n "$message" ] || die "--message is required to commit the pending changes"
  git add -A
  git commit -m "$message"
fi

ahead="$(git rev-list --count "origin/$base..HEAD")"
[ "$ahead" -gt 0 ] || die "no commits on $branch compared to origin/$base; nothing to push"

git push -u origin "$branch"

if [ -n "$no_pr" ]; then echo "Pushed $branch (PR creation skipped)"; exit 0; fi
command -v gh >/dev/null || die "gh CLI not found; branch is pushed, open the PR manually"

if existing="$(gh pr view "$branch" --json url -q .url 2>/dev/null)" && [ -n "$existing" ]; then
  echo "PR already exists (updated with new commits): $existing"; exit 0
fi
args=(--base "$base" --head "$branch" --title "${title:-$message}")
if [ -n "$body_file" ]; then args+=(--body-file "$body_file"); else args+=(--fill-first); fi
[ -z "$draft" ] || args+=(--draft)
gh pr create "${args[@]}"
