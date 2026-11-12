#!/usr/bin/env bash
# Branch, commit, push and open a PR for changes inside a cloned repo (repos/<name>).
#
# Usage (from anywhere in the metarepo, after `git config --local include.path ../.gitconfig`):
#   git create-pr <repo-name> --branch <branch> --message <commit-msg>
#                 [--title <pr-title>] [--body-file <file>] [--base main] [--draft] [--no-pr]
# or call the script directly: skills/create-pr/create-pr.sh <repo-name> ...
#
# - repos/<name> is a plain git clone (git-ignored by the metarepo, made by clone-repo.sh).
# - Pushes to that clone's own `origin`, so code always lands in the right repository.
# - Never pushes to the base branch and never force-pushes.
# - Opens the PR with gh if it is logged in, otherwise with GitHub's API and the token git already
#   uses for this remote (no `gh auth login` needed). Checks this before pushing anything.
# - With --no-pr, or after pushing, prints the compare URL so a PR can be opened in the browser.
set -euo pipefail
# Run as a git alias, git exports GIT_DIR (in a worktree: the metarepo's .git/worktrees/<name>). Left set, every
# git command below would act on the metarepo instead of repos/<name>, even after the cd.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR

die() { echo "Error: $*" >&2; exit 1; }

name="${1:-}"; [ -n "$name" ] && [ "${name#-}" = "$name" ] || die "usage: git create-pr <repo-name> --branch <b> --message <m> [--title <t>] [--body-file <f>] [--draft] [--no-pr]"
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
case "$name" in ""|.|..|*/*) die "invalid repo name: $name" ;; esac
[ -n "$branch" ] || die "--branch is required"
[ "$branch" != "$base" ] || die "branch must differ from base ($base)"
git check-ref-format --branch "$branch" >/dev/null 2>&1 || die "invalid branch name: $branch"
# A git alias runs from the repo root; GIT_PREFIX is the folder the user called it from.
case "$body_file" in ""|/*) ;; *) body_file="$PWD/${GIT_PREFIX:-}$body_file" ;; esac
[ -z "$body_file" ] || [ -f "$body_file" ] || die "body file not found: $body_file"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
dir="$root/repos/$name"
[ -e "$dir/.git" ] || die "repos/$name is not a git clone (clone it with skills/clone-repo/clone-repo.sh <url>)"
cd "$dir"
remote_url="$(git remote get-url origin 2>/dev/null)" || die "repos/$name has no 'origin' remote"
echo "Repository: repos/$name -> $remote_url"

# owner/repo, for the compare URL and for gh
slug="$(printf '%s' "$remote_url" | sed -E 's#^(https?://[^/]+/|git@[^:]+:|ssh://git@[^/]+/)##; s#\.git$##')"

# Open the PR with gh when it is logged in, otherwise with GitHub's API and the token git
# already uses for this remote (github_api.py). Check before pushing anything.
pr_tool=""
if [ -z "$no_pr" ]; then
  case "$remote_url" in *github.com*) ;; *) die "origin is not on GitHub; pass --no-pr to only push" ;; esac
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    pr_tool="gh"
  else
    python3 "$script_dir/github_api.py" check "$slug" || die "can't open PRs: log in with 'gh auth login', or pass --no-pr to only push"
    pr_tool="api"
  fi
fi

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
  secret_files="$(git diff --cached --name-only | grep -E '(^|/)\.env$|(^|/)\.env\.[^e]|keyfile$|\.pem$|id_rsa' || true)"
  if [ -n "$secret_files" ]; then
    git reset --quiet
    die "refusing to commit secrets file(s): $(printf '%s' "$secret_files" | tr '\n' ' '). Add them to .gitignore"
  fi
  if command -v gitleaks >/dev/null; then
    gitleaks protect --staged --no-banner >/dev/null 2>&1 \
      || { git reset --quiet; die "gitleaks found a secret in the staged changes; run 'gitleaks protect --staged' to see it"; }
  fi
  git commit -m "$message"
fi

ahead="$(git rev-list --count "origin/$base..HEAD")"
[ "$ahead" -gt 0 ] || die "no commits on $branch compared to origin/$base; nothing to push"

git push -u origin "$branch"

if [ -n "$no_pr" ]; then
  case "$remote_url" in
    *github.com*) echo "Pushed $branch (PR creation skipped). Open it here: https://github.com/$slug/compare/$base...$branch?expand=1" ;;
    *) echo "Pushed $branch (PR creation skipped)." ;;
  esac
  exit 0
fi

if [ "$pr_tool" = "api" ]; then
  python3 "$script_dir/github_api.py" create "$slug" "$base" "$branch" "${title:-$message}" "$body_file" "${draft:+1}"
  exit 0
fi

state="$(gh pr view "$branch" --repo "$slug" --json state -q .state 2>/dev/null || true)"
if [ "$state" = "OPEN" ]; then
  echo "PR already open (updated with the new commits): $(gh pr view "$branch" --repo "$slug" --json url -q .url)"
  exit 0
fi
args=(--repo "$slug" --base "$base" --head "$branch")
pr_title="${title:-$message}"
[ -z "$pr_title" ] || args+=(--title "$pr_title")
if [ -n "$body_file" ]; then args+=(--body-file "$body_file"); else args+=(--fill-first); fi
[ -z "$draft" ] || args+=(--draft)
gh pr create "${args[@]}"
