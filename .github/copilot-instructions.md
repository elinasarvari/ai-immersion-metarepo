# ai-immersion-metarepo — agent instructions

Central store for shared AI-assisted development assets (see README.md for folder layout).

## Cloned repositories (`repos/`)

- External repositories are cloned into `repos/<repo-name>`. This folder is git-ignored — never commit its contents to the metarepo.
- When the user gives one or more repo URLs to clone/pull in/look at, use the **clone-repo** skill (`skills/clone-repo/SKILL.md`):
  ```bash
  skills/clone-repo/clone-repo.sh <git-url> [folder-name]
  ```
  If the repo already exists, the script fast-forward pulls it instead of re-cloning.
- Never clone outside `repos/`, never embed credentials in URLs, and never delete an existing clone without asking.
- When working inside a cloned repo, follow that repo's own `CLAUDE.md` / rules plus the matching file in `project-rules/`.

## Skills

Skills live in `skills/<name>/SKILL.md`. `.claude/skills` and `.github/skills` are symlinks to `skills/`, so Claude Code and GitHub Copilot share them. Add new skills under `skills/` only.
