# Feature workflow

How a spec becomes merged code in `benefit-be` and `benefit-fe`. [benefit-feature/workflow.yml](benefit-feature/workflow.yml) runs it automatically (`/feature-workflow`). This page explains each stage, and is the manual path (for example in Copilot).

| # | Stage | Who | Output | Checked by (`wf.py`) |
|---|---|---|---|---|
| 0 | Spec | you + `/speckit-specify` (optionally `/speckit-clarify`) | `spec.md` | `prepare` |
| 0b | Clarify | spec-clarifier agent, only if `[NEEDS CLARIFICATION]` markers remain (`decision_mode=auto`) | answered `spec.md`, `clarifications.json` | `clarify-gate` (asks you only for what it left open) |
| 1 | Plan | architect agent (`architecture-plan`) | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `decisions/`, `scope.json` | `plan-gate` |
| 1b | Decide | decision-maker agent, only if an ADR is open (`decision_mode=auto`); architect again if it chose another option | decided ADRs, `decisions/auto-decisions.json` | `decisions-gate`, `plan-gate` |
| 2 | Tasks, then QA | `/speckit-tasks`, then the quality-engineer agent (`test-strategy`) in its own session | `tasks.md` tagged by lane, `test-plan.md` | `tasks-gate` |
| 3 | Contracts | `/speckit-implement` on `[contracts]` tasks, alone | `packages/domain`, OpenAPI, dependencies | verify loop |
| 4 | Lanes and QA tests, in parallel | `/speckit-implement` per lane: tests first, then its unit tests green; beside them, the `[qa]` tests written against the contracts and plan (QA test folders only) | code in each lane's folders, QA tests, `lanes/<lane>/done.json` | verify loop |
| 5 | QA step | `/speckit-implement` on the `[qa]` tasks that needed the lanes' code and the late `[contracts]` tasks, only if there are any | contract, integration, e2e and eval tests wired to the code | `qa-remaining`, verify loop |
| 6 | Verify, while it makes progress (≤6 rounds) | fix (from round 2; later fixes on the judgement model) → the integrator if `origin/main` moved → jobs in parallel: `make check`, builds, evals, `e2e`, `main`, `ownership`, `tasks`, `trace` → if green, the reviews that need it, in parallel | `review/verify.md`, `review/trace.md` | `verify-status`, then `final-gate` |
| 7 | Ship | `create-pr` skill | draft PRs, then GitHub Actions | `ci-wait` |
| 8 | After merge | `sync-repos` skill | clones on the latest `main` | — |

- **Order:** each stage consumes the one before. Contracts go first and alone because every lane depends on them. Lanes run in parallel because they own separate folders (`project-rules/backend-architecture.md`, Ownership).
- **Each check runs once.** A gate follows each planning stage (the skills run the same gate as their self-check, so they can fix their own output first). Every check on the code runs inside the verify loop, so a failure goes to the fix step instead of stopping the run. A round always ends on a verification, so no fix ships unchecked.
- **Reviews** run only once every job passes, so tokens aren't spent reviewing broken code, and later rounds rerun only a review that has no result, still blocks, or whose repo changed. A re-review reads only `wf.py delta` (the change since it last looked).
- **Never a silent pass:** a missing or unreadable result counts as blocking; a job that couldn't run (no `make` target) is a warning in `verify.md` and the PR.
- **Agents:** every AI step is a separate agent session (`agents/README.md`) that works through files; the engine starts them, in parallel where the work is independent.
- **Decisions:** the decision-maker decides each open ADR on the evidence, independently of the architect, and never changes the constitution or a rule set (it picks a compliant option and leaves the amendment as a suggestion). Every automatic decision is listed in the PR for review. The spec clarifier does the same for open spec questions before the plan. `decision_mode=ask` makes both a gate for you instead.
- **Gates for people:** a person is asked only for open spec questions, an ADR with no compliant option, and before pushing when `pr_mode=ask`.
- **Where code goes:** only inside `repos/<repo>`, on `feature/<NNN-feature>` from `origin/main`, in the repos `scope.json` names. Feature 009 may also write the metarepo's `scripts/factory/` and `templates/`.
- **Manual path:** run each stage's skill or command in order. After stages 1, 1b and 2: `wf.py plan-gate`, `decisions-gate`, `tasks-gate`. For 1b by hand, ask the user, or run the decision-maker agent if they want it decided for them. After stage 5: `wf.py job specs/<NNN> <job>` for each of `wf.py jobs specs/<NNN>`, then the **review-changes** skill, then `wf.py verify-status specs/<NNN>`.
- **Models:** judgement steps (spec clarifier, architect, decision-maker, integrator, quality engineer, reviews) use `judgement_model` (default `opus`); steps that follow a written plan (tasks, contracts, lanes, QA, fixes, PRs) use `coding_model` (default `sonnet`).
- **Running it:** `workflows/benefit-feature/run.sh start <NNN> [draft|ask|none]`, then `run.sh watch <NNN>` in a second terminal; `run.sh resume <NNN>` after fixing what stopped it; `run.sh check` for preflight only; `run.sh cleanup <NNN>` after the PRs merge. Always use `run.sh`: it gives the feature its own git worktree (`../ai-immersion-metarepo.worktrees/<NNN-feature>/`, see docs/workflow-architecture.md section 7) and gives the agent steps their permissions.
- **Testing the workflow itself:** `python3 -m unittest discover -s workflows/benefit-feature/tests` runs the tests of every check plus Spec Kit's validator on `workflow.yml`. Run it after any change to either.
