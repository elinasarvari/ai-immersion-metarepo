---
name: clone-repo
description: Clone one or more git repositories (by URL) into the metarepo under repos/. Use when the user gives a GitHub/GitLab/Azure DevOps/Bitbucket repo URL and wants it added, linked, pulled in, or made available in this workspace.
---

# Clone a repo into `repos/`

Linked repositories are **plain git clones** at `repos/<repo-name>`. `repos/*` is gitignored, so the metarepo doesn't track them; each clone keeps its own history and `origin`.

## Steps

1. Collect the repo URL(s) from the user (https or ssh). Optionally a custom folder name.
2. For each URL run, from the metarepo root:

   ```bash
   skills/clone-repo/clone-repo.sh <git-url> [folder-name]
   ```

   If `repos/<name>` is already a clone of that URL, the script runs `git fetch` instead.
3. Tell the user the path (`repos/<name>`). There's nothing to commit in the metarepo.

## Related commands

- Fresh checkout of the metarepo: re-run the script for each project listed in `README.md` ("Projects governed by this repo").
- Update a clone: `git -C repos/<name> pull --ff-only`
- Remove a clone (ask first): `rm -rf repos/<name>`

## Rules

- Never clone anywhere other than `repos/`.
- Don't put credentials in URLs; rely on the user's existing git auth (SSH keys / credential manager). If auth fails, tell the user rather than asking for tokens.
- Never delete or force-replace an existing folder; ask the user first.
- Use the folder-name argument only when two repos share the same name.
