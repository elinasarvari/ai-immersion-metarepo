# ai-immersion-metarepo

Central store for the AI-assisted development assets shared by the Benefit projects:

| Folder | Purpose |
|---|---|
| `workflows/` | Multi-step agent workflows (discover → plan → implement → verify) |
| `skills/` | Reusable skills / slash commands (one folder per skill, with `SKILL.md`) |
| `specs/` | Functional specs and technical plans per feature |
| `project-rules/` | Coding standards and agent rules (e.g. `CLAUDE.md` fragments) per stack |
| `templates/` | Starter templates for specs, plans and rule files |

## Projects governed by this repo

- [benefit-fe](https://github.com/OWNER/benefit-fe) — React frontend
- [benefit-be](https://github.com/OWNER/benefit-be) — Python backend

Each project's `CLAUDE.md` points back to the rules in `project-rules/`.
