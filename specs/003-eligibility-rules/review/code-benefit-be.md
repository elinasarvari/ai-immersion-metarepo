# Code review: benefit-be (003-eligibility-rules)

Scope: `origin/main...HEAD` (5 commits) plus 67 uncommitted files; MERGE=clean, 0 behind. Full review (no earlier result).
Checks run: `uv run pytest tests/packages tests/apps/worker tests/apps/api/test_determinations.py tests/contract` → 601 passed, 13 errors (all in 010/001 Mongo repository tests failing on local Mongo authentication, not this feature's code).

Verdict: **PASS**: 0 critical, 0 major, 3 minor.

| # | Severity | File:line | Problem | Trigger | Fix |
|---|---|---|---|---|---|
| 1 | minor | benefit-be:apps/worker/activities/determination.py:87 | On a duplicate key (`insert` returns False) the activity still returns the summary of the fresh evaluation, not the stored record, so the case summary and the stored `DeterminationRecord` can differ | A retry of `determine_eligibility` that runs after a worker deploy that changed `ENGINE_VERSION` or a rule set entry: the first attempt's record stays stored and the retry returns a summary from the new engine | When `stored` is False, read the existing record by `determination_id` and summarise that one |
| 2 | minor | benefit-be:apps/worker/activities/determination.py:44 | The reason-code mapping (ELIG-06 → `income_over_limit`, else `other_rule_not_met`) is written twice, here and in `apps/api/services/determinations.py:42`, so the case summary and the case-page view can drift apart | A later change to one mapping only (for example a new denial reason) | Move one `reason_code_of(Determination)` into `packages/domain` or `packages/rules` and call it from both places |
| 3 | minor | benefit-be:apps/worker/repositories/snapshots.py:65 | `members_for_year` and `application_form` are tested only through fakes (`tests/apps/worker/eligibility_fakes.py`); nothing checks that real BSON decodes (001's form stores money as `Decimal128` and dates as UTC-midnight datetimes, members are seeded by `db/seeds`) | A seeded or form document shape the models reject would fail every determination at run time, and no test would catch it | Add integration cases in `tests/integration/worker/test_worker_stores.py` that read a seeded member and an `insert_application` form through `MongoSnapshotSource` |

Checked and found sound: income maths and the limit floor (FR-003-15/18), result precedence (FR-003-20), the leap-day age rule, snapshot reuse and the duplicate-key race (TW-11), household and case scoping of every new read and write, the role guard and audit on `GET /cases/{id}/determinations`, the 20-item limit with an index behind it, and no names or household data in logs.
