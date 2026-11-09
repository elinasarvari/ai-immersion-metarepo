#!/usr/bin/env bash
# Clone a git repository into <workspace>/repos/<name>.
# Usage: clone-repo.sh <git-url> [folder-name]
# If the target already exists, it is fast-forward updated instead of re-cloned.
set -euo pipefail

url="${1:-}"
[ -n "$url" ] || { echo "Usage: $0 <git-url> [folder-name]" >&2; exit 2; }

case "$url" in
  https://*|http://*|ssh://*|git@*|git://*) ;;
  *) echo "Error: '$url' does not look like a git URL" >&2; exit 2 ;;
esac

# Workspace root = three levels up from this script (skills/clone-repo/clone-repo.sh)
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
repos_dir="$root/repos"
mkdir -p "$repos_dir"

name="${2:-}"
if [ -z "$name" ]; then
  name="${url%/}"; name="${name%.git}"; name="${name##*/}"; name="${name##*:}"
fi
case "$name" in
  ""|.|..|*/*) echo "Error: invalid folder name '$name'" >&2; exit 2 ;;
esac

target="$repos_dir/$name"
if [ -d "$target/.git" ]; then
  echo "Already cloned: $target — pulling latest"
  git -C "$target" pull --ff-only
elif [ -e "$target" ]; then
  echo "Error: $target exists and is not a git repo" >&2; exit 1
else
  git clone -- "$url" "$target"
fi
echo "Ready: $target"
