# ai-immersion-metarepo — agent instructions

Central store for shared AI-assisted development assets (see README.md for folder layout).

## Linked repositories (`repos/`)

- External repositories are linked as **git submodules** at `repos/<repo-name>`. The metarepo records only the URL and pinned commit (`.gitmodules`), not their files.
- When the user gives one or more repo URLs to add, link or pull in, use the **clone-repo** skill (`skills/clone-repo/SKILL.md`):
  ```bash
  skills/clone-repo/clone-repo.sh <git-url> [folder-name]
  ```
  If the submodule is already registered, the script initialises/updates it instead.
- To check or update the linked repos (after a fresh checkout, after PRs merge, or before starting work), use the **sync-repos** skill: `skills/sync-repos/sync-repos.sh [--check | --commit]`. It only fast-forwards clean submodules on `main` and only records pointers that are merged into `main`.
- Never add submodules outside `repos/`, never embed credentials in URLs, and never remove a submodule without asking.
- When working inside a linked repo, follow that repo's own `CLAUDE.md` / rules plus the rule sets that `project-rules/README.md` maps to the paths you touch. Commits for that project are made inside `repos/<name>`; then commit the updated pointer in the metarepo.
- The project has two repos: `benefit-be` (API, Temporal worker, agents, rules, RAG, MCP servers, DB, evals, analytics) and `benefit-fe` (React UI).

## Rule sets, lane agents and workflows

- **Rule sets** (`project-rules/`): every rule has an ID (`TW-3`, `AG-6`, …). `project-rules/README.md` maps each repo path to its lane and rule files, and says which file wins when two disagree. Generated code must satisfy them; treat them as hard constraints, not suggestions.
- **Lane agents** (`agents/`, shared through the `.claude/agents` and `.github/agents` symlinks): `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane`. They match the four lanes; the three team members rotate between lanes (see `specs/README.md`). They write their lane's section of `plan.md` and review implemented code against their rules. They never edit code.
- **Code reviewers** (`agents/`): `backend-reviewer` (`benefit-be`) and `frontend-reviewer` (`benefit-fe`). They review the whole branch like a senior engineer: bugs, security, tests, spec coverage and the cross-lane rules. They return APPROVE or REQUEST CHANGES with severity-ranked findings, and never edit code. Run them, together with the lane checks, with the **review-changes** skill.
- **Workflows** (`workflows/`): `feature.md` is the standard path from spec to PR. Run it with the **feature-workflow** skill.

## Keeping Claude Code and Copilot in step

Both tools use the same skills, agents and rules. Copilot gets them like this:

| Copilot reads | Comes from | How |
|---|---|---|
| `.github/copilot-instructions.md` | `CLAUDE.md` | generated copy |
| `.github/prompts/<skill>.prompt.md` (slash commands in Copilot Chat) | `skills/<skill>/SKILL.md` | generated |
| `.github/skills/` | `skills/` | symlink |
| `.github/agents/` | `agents/` | symlink |

After changing `CLAUDE.md` or adding, renaming or removing a skill, run `python3 scripts/sync-copilot.py`, and commit the generated files with the change. `--check` reports drift without changing anything. Never edit the generated files directly.

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
- `plan.md` must name the target repo(s) (`repos/<name>`). `/speckit-implement` writes code only inside those submodules, never in the metarepo. The one exception is the software factory, whose plan may also target the metarepo's `scripts/factory/` and `templates/`.
- For backend work, the "Project Structure" section of `plan.md` must use the layout and import boundaries in `project-rules/backend-architecture.md`. Don't invent a different structure.
- `/speckit-plan`: get each affected lane agent's section (plan mode) and include it. `/speckit-tasks`: tag every task with its lane and repo.
- `/speckit-implement`: before each task, read the rule files for its lane. Afterwards, run the **review-changes** skill: every affected lane agent must report PASS and the code reviewer for each changed repo must report APPROVE before any PR is opened.

## Pushing code and opening PRs

When the user asks to push, ship or create a PR, use the **create-pr** skill (`skills/create-pr/SKILL.md`):

```bash
skills/create-pr/create-pr.sh <repo-name> --branch feature/<NNN-feature> --message "<conventional commit>" \
  --title "<pr title>" --body-file <pr-body.md> [--draft]
```

- It runs inside `repos/<name>` and pushes to that submodule's own `origin`, then opens a PR against `main` with `gh` (requires `gh auth login`).
- Branch name = Spec Kit feature folder name with a type prefix (`feature/003-user-login`). Use the same branch in every repo the feature touches, with one PR per repo, and link the PRs to each other.
- Confirm the repo, branch, files and PR title with the user before pushing. Never push to `main`, force-push or skip hooks.
- The metarepo commits only `specs/`, the software factory's `scripts/factory/` and `templates/`, and, after the PRs merge, the updated submodule pointers (`sync-repos.sh --commit`).

## Skills

Skills live in `skills/<name>/SKILL.md`. `.claude/skills` and `.github/skills` are symlinks to `skills/`, so Claude Code and GitHub Copilot share them. Add new skills under `skills/` only.
