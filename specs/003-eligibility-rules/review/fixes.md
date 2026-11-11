# Fixes (verify round 3)

| Test or check | Proves | Why it failed | What changed |
|---|---|---|---|
| `ownership`: `benefit-be:.gitleaks.toml` | BA-1 (each lane's files stay in its folders) | The file is a false positive. Its working-tree and index content are byte-identical to `origin/main`, so `git diff --cached origin/main -- .gitleaks.toml` is empty. But branch commit b14bf98 changed it, and `wf.py changed_files` combined `origin/main...HEAD` (committed history) with `git status` (which reports the revert against HEAD). So a file the feature no longer changes was still counted, and it would stay counted until someone committed, which the fix step isn't allowed to do. | `workflows/benefit-feature/scripts/wf.py` `changed_files` now diffs the working tree (via `tree_id`, untracked included) against `merge-base origin/main HEAD`, which is the change the PR will actually carry. It falls back to the old method when there is no merge base. The check is not loosened: any net change, committed, staged, unstaged or untracked, outside a lane still fails. Doc updated in `docs/workflow-architecture.md`. No benefit-be file changed. |
| `e2e` (warn) | – | Ports 7233, 8233 and 27017 are held by another project's stack (temporal pid 57462, mongod pid 55098). | **environment:** stop that stack to run it locally, or let CI's e2e job run it. |

Regression guard: `workflows/benefit-feature/tests/test_wf.py::ScriptJobs::test_ownership_counts_net_change_not_a_change_reverted_in_the_working_tree`. An unowned file changed in a branch commit fails. Once the working tree puts it back to main's content, it passes. A new untracked unowned file fails again.

No critical or major review findings, open tasks or missing planned tests this round (verify.md: `tasks` and `trace:strict` pass, no review files listed). `lanes/*/blocked.md` work was already done in round 1 (see below).

Checks run: `python3 -m unittest discover -s workflows/benefit-feature/tests` (67 tests, OK) and `wf.py job specs/003-eligibility-rules ownership` (pass, no problems). No file in benefit-be or benefit-fe changed this round, so `make check` (which passed in round 3's jobs) wasn't rerun.

---

# Fixes (verify round 2)

| Test or check | Proves | Why it failed | What changed |
|---|---|---|---|
| `benefit-be:check` → `gitleaks detect --log-opts=HEAD` (18 leaks) | PL-14, security.md (no secrets in commits) | Round 1 restored root `.gitleaks.toml` to main's content (ownership, BA-1), dropping the `known_answers.json` path allowlist. The findings sit in commit b14bf98, which is **on this branch** (not on `origin/main`), so narrowing `--log-opts` can't exclude them. All of them are the `generic-api-key` rule matching the synthetic `case_key` labels (`"KA-02-elig01-out-of-state"`) in `db/seeds/data/known_answers.json` (FR-003-10…13 dataset), not credentials. | New platform-owned `scripts/gitleaks.toml` (default rules + `.env.example` as at root + one allowlist: rule `generic-api-key` AND path `db/seeds/data/known_answers.json` AND match `case_key: "KA-NN-…"`). A real secret anywhere, including elsewhere in that file, is still reported. `Makefile` `check`, `.github/workflows/ci.yml` static job and `scripts/verify.py` pass `--config scripts/gitleaks.toml`. Root `.gitleaks.toml` stays exactly as main has it. `make check`: no leaks found. |
| `ownership`: `benefit-be:.gitleaks.toml` | BA-1 | The branch's committed history changed the root file (b14bf98). The working tree already matches main, so once the branch is committed the file drops out of the diff. | Nothing else needed: the allowlist moved into `scripts/` (platform-ui lane) instead of the root file. |
| `tasks` T032 | FR-003-02, -14, -19, -23; SC-003-02; TC-129, TC-130 | The task was left open in round 1 because the journey test couldn't run here. | `openapi/openapi.json` is regenerated (`make openapi-check` passes against the staged tree, which is how the job runs it). `tests/integration/test_determination_journey.py` holds TC-129 and TC-130. Marked `[X]`. **environment:** running it needs MongoDB with this worktree's credentials and Temporal on 7233. Here 27017 is another stack's mongod (pid 55098: `OperationFailure`, auth rejected) and 7233 is another Temporal (pid 57462). CI's integration job runs it. |
| `tasks` lanes/{data,platform-ui,workflows}-lane/blocked.md | (see each file) | These are only reported while a task is open (wf.py:453). Everything they list was built in round 1: migration 0005 and its test, `verifications.py`, `history.py`, `test_sets.py` with `test_test_sets.py`, `Scope.for_worker`, `seeded_verifications` scope, the determinations route and `listCaseDeterminations` in openapi, and no `EligibilityResult` left. | No code change. The files are now historical. |
| `e2e` (warn) | – | Ports 7233, 8233 and 27017 are held by another project's stack. | **environment:** stop that stack to run it locally, or let CI's e2e job run it. |

Regression guard: `tests/contract/test_ci_workflow.py::test_every_secrets_scan_uses_the_narrow_gitleaks_config` checks that every gitleaks call (Makefile, CI, verify.py) uses `--config scripts/gitleaks.toml --log-opts=HEAD`. It also checks that the config allows only `.env.example` by path, that the label exception is `generic-api-key` AND path AND match, and that its regex matches a `KA-` label but not a key-shaped value.

There were no critical or major review findings to fix this round (verify.md lists no review files).

Checks run: `make check` in benefit-be passes (ruff, mypy, 547 unit, 136 workflow, 27 contract, openapi-check, gitleaks, pip-audit). It ran with the tree staged, as `wf.py` jobs do, and the index was restored afterwards. benefit-fe is unchanged.

---

Round 1: per-lane detail in [fixes-contracts-ui.md](fixes-contracts-ui.md), [fixes-data.md](fixes-data.md) and [fixes-workflows.md](fixes-workflows.md). T001–T003, T011–T012 and T015–T028 were built, TC-68–87 added, and the ruff E501 errors fixed.
