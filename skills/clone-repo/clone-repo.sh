#!/usr/bin/env bash
# Clone a git repository into <metarepo>/repos/<name> (a plain local clone, ignored by the metarepo).
# Usage: clone-repo.sh <git-url> [folder-name]
# If the folder is already a clone of the same URL, it fetches the latest changes instead.
set -euo pipefail

url="${1:-}"
[ -n "$url" ] || { echo "Usage: $0 <git-url> [folder-name]" >&2; exit 2; }

case "$url" in
  https://*|http://*|ssh://*|git@*|git://*) ;;
  *) echo "Error: '$url' does not look like a git URL" >&2; exit 2 ;;
esac

# Metarepo root = two levels up from this script (skills/clone-repo/clone-repo.sh)
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
mkdir -p "$root/repos"

name="${2:-}"
if [ -z "$name" ]; then
  name="${url%/}"; name="${name%.git}"; name="${name##*/}"; name="${name##*:}"
fi
case "$name" in
  ""|.|..|*/*) echo "Error: invalid folder name '$name'" >&2; exit 2 ;;
esac

dir="$root/repos/$name"
if [ -e "$dir/.git" ]; then
  existing="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
  [ "${existing%.git}" = "${url%.git}" ] \
    || { echo "Error: $dir is already a clone of '$existing', not '$url'" >&2; exit 1; }
  echo "Already cloned: repos/$name — fetching latest"
  git -C "$dir" fetch origin --prune
elif [ -e "$dir" ]; then
  echo "Error: $dir exists but is not a git repository" >&2; exit 1
else
  git clone -- "$url" "$dir"
fi
echo "Ready: $dir"
