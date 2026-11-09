# ai-immersion-metarepo — agent instructions

Central store for shared AI-assisted development assets (see README.md for folder layout).

## Linked repositories (`repos/`)

- External repositories are **plain git clones** at `repos/<repo-name>`. `repos/*` is gitignored, so the metarepo doesn't track them.
- When the user gives one or more repo URLs to add, link or pull in, use the **clone-repo** skill (`skills/clone-repo/SKILL.md`):
  ```bash
  skills/clone-repo/clone-repo.sh <git-url> [folder-name]
  ```
  If the folder is already a clone of that URL, the script fetches the latest changes instead.
- After a fresh checkout of the metarepo, run the script once for each project listed in README.md.
- Never clone outside `repos/`, never embed credentials in URLs, and never delete a clone without asking.
- When working inside a linked repo, follow that repo's own `CLAUDE.md` / rules plus the matching file in `project-rules/`. Commits for that project are made inside `repos/<name>`; the metarepo has nothing to commit for them.

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
- When building one of the linked projects, work inside `repos/<name>` and use that project's own build and test commands.
- Don't edit `.specify/templates` or `.specify/scripts` unless asked. Update them with `specify integration upgrade`.
- `plan.md` must name the target repo(s) (`repos/<name>`). `/speckit-implement` writes code only inside those clones, never in the metarepo.
- For backend work, the "Project Structure" section of `plan.md` must use the layout and import boundaries in `project-rules/backend-architecture.md`. Don't invent a different structure.
- `/speckit-plan`: get each affected lane agent's section (plan mode) and include it. `/speckit-tasks`: tag every task with its lane and repo.
- `/speckit-implement`: before each task, read the rule files for its lane. Afterwards, every affected lane agent must review the changes (review mode) and report PASS before any PR is opened.

## Pushing code and opening PRs

When the user asks to push, ship or create a PR, use the **create-pr** skill (`skills/create-pr/SKILL.md`):

```bash
skills/create-pr/create-pr.sh <repo-name> --branch feature/<NNN-feature> --message "<conventional commit>" \
  --title "<pr title>" --body-file <pr-body.md> [--draft]
```

- It runs inside `repos/<name>` and pushes to that clone's own `origin`, then opens a PR against `main` with `gh` (requires `gh auth login`).
- Branch name = Spec Kit feature folder name with a type prefix (`feature/003-user-login`). Use the same branch in every repo the feature touches, with one PR per repo, and link the PRs to each other.
- Confirm the repo, branch, files and PR title with the user before pushing. Never push to `main`, force-push or skip hooks.
- The metarepo commits only `specs/`. After the PRs merge, refresh each clone with `git -C repos/<name> pull --ff-only` on `main`.

## Skills

Skills live in `skills/<name>/SKILL.md`. `.claude/skills` and `.github/skills` are symlinks to `skills/`, so Claude Code and GitHub Copilot share them. Add new skills under `skills/` only.
