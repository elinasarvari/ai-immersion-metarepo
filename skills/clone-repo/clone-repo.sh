#!/usr/bin/env bash
# Add a git repository as a submodule at <metarepo>/repos/<name>.
# Usage: clone-repo.sh <git-url> [folder-name]
# If the submodule is already registered, it is initialised/updated instead.
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

path="repos/$name"
if git -C "$root" config -f .gitmodules --get "submodule.$path.url" >/dev/null 2>&1; then
  echo "Submodule already registered: $path — initialising/updating"
  git -C "$root" submodule update --init -- "$path"
elif [ -e "$root/$path" ]; then
  echo "Error: $root/$path exists but is not a registered submodule" >&2; exit 1
else
  git -C "$root" submodule add -- "$url" "$path"
fi
echo "Ready: $root/$path (commit .gitmodules and $path to record it)"
