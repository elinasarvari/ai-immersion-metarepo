#!/usr/bin/env bash
# Check and sync the submodules under repos/ to the latest default branch (usually main).
#
# Usage: sync-repos.sh [--check] [--commit] [repo-name ...]
#   (no flags)  validate .gitmodules, init missing submodules, fast-forward clean ones to origin/<default>
#   --check     validate and report only; change nothing; exit 1 if anything is wrong or behind
#   --commit    after syncing, commit the updated submodule pointers in the metarepo
#
# Safety: a submodule is only moved when its working tree is clean and it is on the default
# branch (or detached at a commit already contained in it). Feature branches, local changes and
# unpushed commits are reported and left alone. Never force, never reset.
set -uo pipefail

check="" commit="" only=()
for a in "$@"; do
  case "$a" in
    --check) check=1 ;;
    --commit) commit=1 ;;
    -*) echo "unknown option: $a" >&2; exit 2 ;;
    *) only+=("repos/$a") ;;
  esac
done
[ -z "$check" ] || [ -z "$commit" ] || { echo "--check and --commit can't be combined" >&2; exit 2; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(cd "$script_dir/../.." && pwd -P)"
cd "$root"

problems=0 behind=0 updated=() skipped=()
ok()   { printf '  ✓ %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*"; }
bad()  { printf '  ✗ %s\n' "$*"; problems=$((problems+1)); }

echo "== Validating .gitmodules"
paths=()
if [ -f .gitmodules ]; then
  while read -r key p; do
    name="${key#submodule.}"; name="${name%.path}"
    paths+=("$p")
    case "$p" in repos/*) ;; *) bad "$p: submodule outside repos/" ;; esac
    url="$(git config -f .gitmodules --get "submodule.$name.url" || true)"
    [ -n "$url" ] || bad "$p: no url in .gitmodules"
    [ "$(git ls-files --stage -- "$p" | cut -c1-6)" = "160000" ] || bad "$p: in .gitmodules but not recorded in the index (run: git submodule add)"
    local_url="$(git config --get "submodule.$name.url" || true)"
    if [ -n "$local_url" ] && [ "$local_url" != "$url" ]; then
      if [ -n "$check" ]; then bad "$p: local URL differs from .gitmodules (run sync to fix)"
      else git submodule sync -q -- "$p" && ok "$p: URL re-synced from .gitmodules"; fi
    fi
  done < <(git config -f .gitmodules --get-regexp '^submodule\..*\.path$')
fi
[ ${#paths[@]} -gt 0 ] || { echo "No submodules registered. Add one with skills/clone-repo/clone-repo.sh"; exit 0; }

# Folders in repos/ that aren't registered submodules
for d in repos/*/; do
  [ -d "$d" ] || continue; d="${d%/}"
  printf '%s\n' "${paths[@]}" | grep -qx "$d" || bad "$d: folder in repos/ is not a registered submodule"
done

[ ${#only[@]} -eq 0 ] || paths=("${only[@]}")

echo "== Syncing submodules"
for p in "${paths[@]}"; do
  echo "-- $p"
  if [ ! -e "$p/.git" ]; then
    if [ -n "$check" ]; then bad "not initialised (run: git submodule update --init $p)"; continue; fi
    git submodule update --init -q -- "$p" || { bad "init failed"; continue; }
    ok "initialised"
  fi
  if ! git -C "$p" fetch -q origin; then bad "fetch failed (auth/network?)"; continue; fi
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

echo "== Metarepo pointers"
# Only pointers that are already merged into the submodule's default branch may be recorded.
safe=()
for p in $(git diff --name-only -- "${paths[@]}"); do
  def="$(git -C "$p" symbolic-ref --short -q refs/remotes/origin/HEAD || echo origin/main)"
  if git -C "$p" merge-base --is-ancestor HEAD "$def" 2>/dev/null; then
    safe+=("$p")
  else
    warn "$p: checked-out commit isn't merged into $def yet; its pointer won't be recorded"
  fi
done
if [ ${#safe[@]} -eq 0 ]; then ok "no merged pointer changes to record"
else
  git --no-pager diff --submodule=log -- "${safe[@]}" | sed 's/^/  /'
  if [ -n "$commit" ]; then
    git add -- "${safe[@]}" && git commit -q -m "chore(repos): sync submodules to latest default branch" -- "${safe[@]}" \
      && ok "committed pointer update for: ${safe[*]}" || bad "commit failed"
  else
    echo "  Record with: git add ${safe[*]} && git commit -m 'chore(repos): sync submodules'  (or rerun with --commit)"
  fi
fi

echo "== Summary: ${#updated[@]} updated, ${#skipped[@]} left alone, $behind behind, $problems problem(s)"
[ "$problems" -eq 0 ] && { [ -z "$check" ] || [ "$behind" -eq 0 ]; }
