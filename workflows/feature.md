# Feature workflow

How a spec becomes merged code in `benefit-be` and `benefit-fe`. [benefit-feature/workflow.yml](benefit-feature/workflow.yml) runs it automatically (`/feature-workflow`). This page explains each stage, and is the manual path (for example in Copilot).

| # | Stage | Who | Output | Checked by (`wf.py`) |
|---|---|---|---|---|
| 0 | Spec | you + `/speckit-specify`, `/speckit-clarify` | `spec.md` | `spec-check` (asks you if questions remain) |
| 1 | Plan | architect role (`architecture-plan`) | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `decisions/`, `scope.json` | `plan-check`, `decisions-check`, `scope-check` (asks you if a decision is yours) |
| 2 | Tasks + QA | `/speckit-tasks`, then quality engineer role (`test-strategy`) | `tasks.md` tagged by lane, `test-plan.md` | `tasks-split`, `test-plan-check` |
| 3 | Contracts | `/speckit-implement` on `[contracts]` tasks, alone | `packages/domain`, OpenAPI, dependencies | — |
| 4 | Lanes, in parallel | `/speckit-implement` per lane (tests first), then its unit tests and fixes | code in each lane's folders | `lane-tests` |
| 5 | QA tests | `/speckit-implement` on `[qa]` tasks | contract, integration, e2e and eval tests | `ownership` |
| 6 | Verify, ≤3 rounds | jobs in parallel (`make check`, builds, evals) → if green, code reviewers + compliance review in parallel → fix | `review/verify.md` | `verify-status` |
| 7 | Trace | script | `review/trace.md` | `trace` (every FR has a named test) |
| 8 | Ship | `create-pr` skill | draft PRs, then GitHub Actions | `ci-wait` |
| 9 | After merge | `sync-repos` skill | clones on the latest `main` | — |

- **Order:** each stage consumes the one before. Contracts go first and alone because every lane depends on them. Lanes run in parallel because they own separate folders (`project-rules/backend-architecture.md`, Ownership). Reviews run only once tests and builds pass, so tokens aren't spent reviewing broken code.
- **Gates:** a person is asked only for open spec questions, decisions that are theirs (product, policy, cost, rule changes), and before pushing when `pr_mode=ask`.
- **Where code goes:** only inside `repos/<repo>`, on `feature/<NNN-feature>` from `origin/main`. Feature 009 may also write the metarepo's `scripts/factory/` and `templates/`.
- **Manual path:** run each stage's skill or command in order, then the matching `python3 workflows/benefit-feature/scripts/wf.py <check> specs/<NNN-feature>`.
