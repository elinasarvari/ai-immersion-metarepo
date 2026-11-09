# ai-immersion-metarepo

Central store for the AI-assisted development assets shared by the Benefit projects:

| Folder | Purpose |
|---|---|
| `workflows/` | Multi-step agent workflows (spec → plan → implement → rules gate → PR) |
| `agents/` | Lane agents (Workflows, Agents, Knowledge & data, Platform & UI) that plan and review against the rule sets |
| `skills/` | Reusable skills / slash commands (one folder per skill, with `SKILL.md`) |
| `specs/` | Functional specs and technical plans per feature |
| `project-rules/` | Rule sets with IDs, mapped to repo paths in `project-rules/README.md` |
| `templates/` | Starter templates for specs, plans and rule files |

## Projects governed by this repo

- [benefit-fe](https://github.com/OWNER/benefit-fe) — React frontend
- [benefit-be](https://github.com/OWNER/benefit-be) — Python backend

Each project's `CLAUDE.md` points back to the rules in `project-rules/`.

## Linked repositories

Project repos are git submodules under `repos/`. Ask Claude Code or GitHub Copilot to "add <url>", or run directly:

```bash
skills/clone-repo/clone-repo.sh https://github.com/OWNER/benefit-fe.git
```

After cloning this metarepo, fetch them with `git submodule update --init --recursive`.

`.claude/skills` and `.github/skills` are symlinks to `skills/`, so both tools discover the same skills.

## Pushing changes and opening PRs

Code generated with Spec Kit is written inside `repos/<name>`. To ship it, ask the agent to "create a PR", or run:

```bash
skills/create-pr/create-pr.sh benefit-fe --branch feature/001-login --message "feat(login): add login page" --title "feat(login): add login page"
```

This branches from `origin/main` in that submodule, commits, pushes to the submodule's own remote and opens a PR against `main` (requires `gh auth login`).

## Claude Code and GitHub Copilot

Both tools share `skills/`, `agents/` and `project-rules/`. Copilot's own files (`.github/copilot-instructions.md` and the slash commands in `.github/prompts/`) are generated from `CLAUDE.md` and the skills:

```bash
python3 scripts/sync-copilot.py          # regenerate
python3 scripts/sync-copilot.py --check  # fail if out of date
```
