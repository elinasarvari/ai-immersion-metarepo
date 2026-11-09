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

## Spec-driven development (GitHub Spec Kit)

Spec Kit is set up in `.specify/`, which holds its templates, bash scripts and the constitution (`.specify/memory/constitution.md`). Feature specs, plans and tasks go in `specs/<NNN-feature>/`.

Run these steps in order. In Claude Code they are slash commands; in Copilot, ask it to use the skill with that name.

1. `/speckit-constitution`: set the project principles, based on `project-rules/`
2. `/speckit-specify <what to build>`: write the functional spec
3. `/speckit-clarify` *(optional)*: resolve unclear points
4. `/speckit-plan <tech choices>`: write the technical plan
5. `/speckit-checklist` *(optional)*: generate a quality checklist
6. `/speckit-tasks`: break the plan into tasks
7. `/speckit-analyze` *(optional)*: check the spec, plan and tasks are consistent
8. `/speckit-implement`: build it by working through the tasks and running the needed install, build and test commands
9. `/speckit-converge`: find remaining gaps and add them as tasks

Rules:
- Run the `.specify/scripts/bash/*.sh` scripts exactly as the skills say. Don't create feature folders by hand.
- When building one of the cloned projects, work inside `repos/<name>` and use that project's own build and test commands.
- Don't edit `.specify/templates` or `.specify/scripts` unless asked. Update them with `specify integration upgrade`.

## Skills

Skills live in `skills/<name>/SKILL.md`. `.claude/skills` and `.github/skills` are symlinks to `skills/`, so Claude Code and GitHub Copilot share them. Add new skills under `skills/` only.
