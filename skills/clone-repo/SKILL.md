---
name: clone-repo
description: Clone one or more git repositories (by URL) into the workspace's repos/ folder. Use when the user gives a GitHub/GitLab/Azure DevOps/Bitbucket repo URL and wants it cloned, pulled in, or made available for reading in this workspace.
---

# Clone repo into `repos/`

Clones repositories into `<workspace>/repos/<repo-name>`. The `repos/` folder is git-ignored, so cloned repos never get committed to the metarepo.

## Steps

1. Collect the repo URL(s) from the user (https or ssh). Optionally a custom folder name.
2. For each URL run, from the workspace root:

   ```bash
   skills/clone-repo/clone-repo.sh <git-url> [folder-name]
   ```

3. Report the resulting path(s) (`repos/<name>`). If the repo was already cloned, the script fast-forward pulls it instead.

## Rules

- Never clone anywhere other than `repos/`.
- Don't pass credentials in URLs; rely on the user's existing git auth (SSH keys / credential manager). If auth fails, tell the user rather than asking for tokens.
- Never `rm -rf` an existing folder to force a re-clone; ask the user first.
- Use the folder-name argument only when two repos share the same name.
