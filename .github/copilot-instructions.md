# ai-immersion-metarepo — agent instructions

Central store for shared AI-assisted development assets (see README.md for folder layout).

## Linked repositories (`repos/`)

- External repositories are plain git clones at `repos/<repo-name>`. `repos/` is git-ignored: the metarepo never commits their files and there are no submodules or `.gitmodules`.
- When the user gives one or more repo URLs to add, link or pull in, use the **clone-repo** skill (`skills/clone-repo/SKILL.md`):
  ```bash
  skills/clone-repo/clone-repo.sh <git-url> [folder-name]
  ```
  If the clone already exists, the script fast-forward pulls it instead.
- To check or update the clones (after a fresh checkout, after PRs merge, or before starting work), use the **sync-repos** skill: `skills/sync-repos/sync-repos.sh [--check]`. It only fast-forwards clean clones on `main`, and leaves feature branches and local changes alone.
- Never clone outside `repos/`, never embed credentials in URLs, and never delete a clone without asking.
- When working inside a cloned repo, follow that repo's own `CLAUDE.md` / rules plus the rule sets that `project-rules/README.md` maps to the paths you touch. Commits for that project are made inside `repos/<name>` and pushed to its own `origin`.
- The project has two repos: `benefit-be` (API, Temporal worker, agents, rules, RAG, MCP servers, DB, evals, analytics) and `benefit-fe` (React UI).

## Rules, roles, agents and workflows

- **Rule sets** (`project-rules/`): every rule has an ID (`TW-3`, `AG-6`, …). `project-rules/README.md` maps each repo path to its lane and rule files. Generated code must satisfy them as hard constraints. Lanes (workflows, agents, data, platform-ui) are folder ownership, used for parallel work and rule mapping; three team members rotate between them (`specs/README.md`).
- **Roles and agents** (`agents/`, summary and shared conventions in `agents/README.md`):
  - **architect** (role): plans the feature and records significant decisions as ADRs. Skills: `architecture-plan`, `architecture-decision`, `architecture-capabilities`.
  - **quality-engineer** (role): the test plan, and test and QA tasks. Skill: `test-strategy`.
  - **compliance-reviewer** (role): checks the implementation against the constitution, rules, ADRs and test plan. Skill: `compliance-review`.
  - **backend-reviewer**, **frontend-reviewer** (agents): senior code review per repo.

  A role is `rules/behavior.md` plus `skills/`; whoever runs one of its skills takes it on, bound by that behavior file. Never mark a `Needs decision` or `Proposed – needs amendment` ADR as accepted without the user's explicit answer.
- **Workflows** (`workflows/`): `feature.md` describes the stages. `benefit-feature/workflow.yml` runs them from an existing spec with Spec Kit's workflow engine:
  1. architect plan
  2. tasks and QA tasks
  3. contracts
  4. lanes in parallel (`lane-chain/workflow.yml`), then QA tests
  5. verify loop: tests and builds in parallel, then code and compliance reviews in parallel, then fix
  6. traceability
  7. draft PRs, then GitHub Actions

  A script check (`benefit-feature/scripts/wf.py`) follows every stage. It asks a person only for open spec questions, decisions that are theirs, or before pushing with `pr_mode=ask`. Start, resume or check a run with the **feature-workflow** skill. Never answer a gate (`spec_verdict`, `decision_verdict`, `pr_verdict`) unless the user explicitly decided what it shows.
- **Docs:** `docs/workflow-architecture.md` explains the workflow with Mermaid diagrams. Update it in the same change whenever the workflow, roles, agents or gates change.
- **Token economy:** follow `agents/README.md`. Read only the mapped rule files and the diff, write results to files, reply briefly, and on re-reviews read only what changed.

## Keeping Claude Code and Copilot in step

Both tools use the same skills, agents and rules. Copilot gets them like this:

| Copilot reads | Comes from | How |
|---|---|---|
| `.github/copilot-instructions.md` | `CLAUDE.md` | generated copy |
| `.github/prompts/<skill>.prompt.md` (slash commands in Copilot Chat) | each skill's `SKILL.md` | generated |
| `.claude/skills/<name>`, `.github/skills/<name>` | `skills/<name>/` and `agents/<agent>/skills/<name>/` | generated symlink, one per skill |
| `.claude/agents/<name>.agent.md`, `.github/agents/<name>.agent.md` | `agents/**/<name>.agent.md` | generated symlink, one per agent file |

After changing `CLAUDE.md`, or adding, renaming or removing a skill or an agent, run `python3 scripts/sync-copilot.py`, and commit the generated files with the change. `--check` reports drift without changing anything. Never edit the generated files directly.

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
- `plan.md` must name the target repo(s) (`repos/<name>`). `/speckit-implement` writes code only inside those clones, never in the metarepo. The one exception is feature 009 (delivery factory), whose plan may also target the metarepo's `scripts/factory/` and `templates/`.
- For backend work, the "Project Structure" section of `plan.md` must use the layout and import boundaries in `project-rules/backend-architecture.md`. Don't invent a different structure.
- Plan through the **architecture-plan** skill rather than a bare `/speckit-plan`; it adds the decisions and scope. After `/speckit-tasks`, run the **test-strategy** skill. Tag every task with one lane and its repo (`[contracts]`, `[workflows]`, `[agents]`, `[data]`, `[platform-ui]`, `[qa]`).
- `/speckit-implement`: before each task, read the rule files for its lane. Before any PR, the code reviewers and the compliance review (**review-changes** skill) must have no critical or major findings.

## Pushing code and opening PRs

When the user asks to push, ship or create a PR, use the **create-pr** skill (`skills/create-pr/SKILL.md`):

```bash
git create-pr <repo-name> --branch feature/<NNN-feature> --message "<conventional commit>" \
  --title "<pr title>" --body-file <pr-body.md> [--draft]
```

`git create-pr` is a git alias for `skills/create-pr/create-pr.sh`, defined in the committed `.gitconfig`. Enable it once per clone of the metarepo with `git config --local include.path ../.gitconfig`.

- It runs inside `repos/<name>` and pushes to that clone's own `origin`, then opens a PR against `main`: with `gh` if it is logged in, otherwise through GitHub's API with the token git already uses. With `--no-pr` it only pushes and prints the compare link.
- Branch name = Spec Kit feature folder name with a type prefix (`feature/003-user-login`). Use the same branch in every repo the feature touches, with one PR per repo, and link the PRs to each other.
- Confirm the repo, branch, files and PR title with the user before pushing, unless the push is part of a `benefit-feature` run the user started with `pr_mode=draft`; that start is their approval. Never push to `main`, force-push or skip hooks.
- The metarepo commits only its own files (`specs/`, feature 009's `scripts/factory/`, `templates/`, rules and skills), never the clones. After the PRs merge, fast-forward the clones with `sync-repos.sh`.

## Skills

Shared skills live in `skills/<name>/SKILL.md`. A skill that belongs to one agent or role lives only in that folder, as `agents/<agent>/skills/<name>/SKILL.md` (see `agents/architect/`); don't copy or link it into `skills/`. `.claude/skills/` and `.github/skills/` hold one generated link per skill from both places, so both tools find all of them. Inside skill files, write paths from the metarepo root, because they're read through those links.

Agents are `*.agent.md` files anywhere under `agents/`. `.claude/agents/` and `.github/agents/` hold one generated link per agent file, so neither tool loads an agent's or role's `rules/` or `skills/` files as agents. Never link the whole `agents/` or `skills/` folder; run `python3 scripts/sync-copilot.py` instead.
