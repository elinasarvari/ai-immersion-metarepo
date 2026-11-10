# data-lane: notes for other lanes (001-case-lifecycle)

No data-lane task is blocked. These need action outside `db/` / `tests/db/`:

## 1. Platform & UI: `test_FR_000_19_no_unscoped_queries_on_household_collections` fails

`tests/db/test_scope.py` scans `apps/` and `packages/` for direct collection access. The in-progress
`apps/api/repositories/cases.py` uses `db["cases"]`, `db["review_tasks"]`, … (5 hits). Go through
`packages/platform/scope.py` (`find_one` / `find_many` / scoped writes) or extend the scan's allow
list in a [contracts]/platform change. Not changed by the data lane.

## 2. Workflows + Platform & UI: what migration `0002_case_lifecycle` enforces

Writers of `cases`, `case_events`, `review_tasks`, `caseworker_actions`, `coverage_periods` and
`outbox` (`apps/worker/repositories/cases.py`, `apps/api/repositories/cases.py`) must match it:

- `additionalProperties: false`: only the data-model.md fields, plus optional `created_at` / `updated_at`.
- IDs are BSON UUIDs (binData); optional fields may be `null` (a `model_dump()` with `None` is fine).
- Calendar dates (`received_on`, `decision_deadline`, `decided_on`, `start_date`, `end_date`) are BSON
  dates at midnight UTC. PyMongo cannot encode `datetime.date`, so convert before writing.
- `cases.open` must be `false` exactly when `state == "decided"` (the validator rejects other pairs).
- `case_events.reason_code`, `review_tasks.evidence.missing_items` and `failed_rules` are snake_case
  codes (`^[a-z0-9_]+$`, ≤ 64 chars), never free text.
- `outbox.notice_type` is `approval` | `denial`, and `status` is `requested` (011 widens these).
- Index names: `submission_reference_unique`, `household_open_unique` (partial, `open: true`),
  `state_deadline`, `case_seq_unique`, `status_opened`, `household_end_date`.

## 3. Workflows (T010): the stub field

The seed sets `households.stub_result` to `eligible` | `ineligible` | `cannot_determine`
(`DeterminationOutcome` values): household-a (`applicant1`) eligible, household-b (`applicant2`)
ineligible, household-c (`applicant3`, new) cannot_determine. The stubs may read it (research R1).

## 4. Existing 000 tests changed in this lane's folders

- `tests/db/seeds/test_users.py`, `tests/db/seeds/test_reset.py`: they now expect the third seeded
  household and the `applicant3` account that TC-29 needs.
- `tests/db/test_migrations.py`: the runner test now expects `0002_case_lifecycle` to be recorded.
- `tests/db/test_scope.py`: the fixture case documents now pass the 0002 validator.
