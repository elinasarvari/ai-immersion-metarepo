---
name: clone-repo
description: Add one or more git repositories (by URL) to the metarepo as git submodules under repos/. Use when the user gives a GitHub/GitLab/Azure DevOps/Bitbucket repo URL and wants it added, linked, pulled in, or made available in this workspace.
---

# Add repo as a submodule under `repos/`

Repositories are linked as **git submodules** at `repos/<repo-name>`. The metarepo records only the URL (in `.gitmodules`) and the pinned commit, not the repo's files.

## Steps

1. Collect the repo URL(s) from the user (https or ssh). Optionally a custom folder name.
2. For each URL run, from the metarepo root:

   ```bash
   skills/clone-repo/clone-repo.sh <git-url> [folder-name]
   ```

   If the submodule is already registered, the script runs `git submodule update --init` for it instead.
3. Tell the user the path (`repos/<name>`) and that `.gitmodules` plus `repos/<name>` are staged and ready to commit. Commit only if the user asks.

## Related commands

- Fresh checkout of the metarepo: `git submodule update --init --recursive`
- Move every submodule to its latest remote commit: `git submodule update --remote`
- Remove a submodule (ask first): `git submodule deinit -f repos/<name> && git rm -f repos/<name>`

## Rules

- Never add submodules anywhere other than `repos/`.
- Don't put credentials in URLs; rely on the user's existing git auth (SSH keys / credential manager). If auth fails, tell the user rather than asking for tokens.
- Never delete or force-replace an existing folder; ask the user first.
- Use the folder-name argument only when two repos share the same name.
