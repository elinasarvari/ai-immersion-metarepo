# Feature workflow: spec → plan → implement → rules gate → PR

The standard path for any feature in `benefit-be` and/or `benefit-fe`. Each step names who does it and what must be true before moving on.

## 0. Prepare
- The repos are linked: `repos/benefit-be`, `repos/benefit-fe` (`clone-repo` skill).
- Run `skills/sync-repos/sync-repos.sh` (`sync-repos` skill) so both repos are initialised and on the latest `main`.
- **Gate:** no problems reported. Any repo left alone is either the one this feature continues, or the user has decided what to do with it.

## 1. Specify (main assistant)
- `/speckit-specify <what to build>`, then `/speckit-clarify` if anything is unclear.
- **Gate:** `spec.md` has no open `[NEEDS CLARIFICATION]` markers.

## 2. Plan (main assistant + lane agents)
1. Decide which lanes the feature touches (see the map in `project-rules/README.md`).
2. Ask each affected lane agent, in plan mode, for its section: `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane`. They can run in parallel.
3. `/speckit-plan` with those sections. `plan.md` must include:
   - **Target repos:** `repos/benefit-be` and/or `repos/benefit-fe`
   - **Project structure** following `project-rules/backend-architecture.md` and `project-rules/frontend-ui.md`
   - **Contracts** between lanes (`packages/domain` models, signals, MCP tools, API endpoints) and any OpenAPI change (`PL-3`)
   - **Rules at risk:** the rule IDs each lane flagged
4. `/speckit-checklist` (optional).
- **Gate:** every lane in scope has a section, and contracts are agreed before any code is written.

## 3. Tasks (main assistant)
- `/speckit-tasks`. Tag every task with its lane and repo, for example `[workflows][benefit-be]`.
- Order the work: contracts in `packages/domain` first, then each lane's tasks, with the tests written before the implementation (`testing.md`).
- `/speckit-analyze` to check the spec, plan and tasks are consistent.
- **Gate:** no task without a lane tag; no lane task without its required tests.

## 4. Implement (main assistant)
- `/speckit-implement`. Code is written only inside `repos/<repo>`.
- Before writing each task, read the rule files for that task's lane. Follow them as hard constraints.
- Work on a feature branch in each repo (`feature/<NNN-feature>`), created from `origin/main`.

## 5. Rules gate (lane agents, review mode)
1. Ask each lane agent whose paths changed to review the branch.
2. Any FAIL: fix the cited violations, then ask only the failing lanes to review again.
3. Repeat until every lane reports PASS.
- **Gate:** every affected lane reports PASS. Don't open a PR with a known violation.

## 6. Verify (main assistant)
- `make check` in each changed repo (`benefit-be`: ruff, mypy, pytest, gitleaks, pip-audit; `benefit-fe`: ESLint, Prettier, `tsc`, Vitest, Playwright, `pnpm audit`).
- `make eval` if agents, retrieval or extraction changed (`AG-17`, `KD-8`).
- `/speckit-converge` to find anything in the spec that isn't built yet. If it adds tasks, go back to step 4.
- **Gate:** all checks pass and eval scores are at or above the thresholds.

## 7. Pull requests (`create-pr` skill)
- One PR per changed repo, using the same branch name, filled from the PR template.
- Include in each PR: the lane review results (PASS per lane), check and eval results, and links to the sibling PR.
- If the OpenAPI spec changed, open the `benefit-be` PR first, then the `benefit-fe` PR that regenerates the client.
- Confirm with the user before pushing.

## 8. After merge
- Run `skills/sync-repos/sync-repos.sh --commit` (`sync-repos` skill). It fast-forwards each repo to the merged `main` and commits the new pointers. Feature branches still in progress are left alone and not recorded.
- Commit the feature's `specs/` folder in the metarepo.
