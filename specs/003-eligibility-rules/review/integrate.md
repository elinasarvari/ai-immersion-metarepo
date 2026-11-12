# Integrate: origin/main → feature/003-eligibility-rules (2026-11-10)

## benefit-be

**Commits:** `02c3809` wip(003) (the feature's uncommitted work), then merge commit `08199ed`. Not pushed.

**Merged from main (9):** PR #2 `feature/001-case-lifecycle` (`e491bce`, `d6d19fc`, `5d9cd01`, `1caf572`, `4bb7b97`, `f361779`, `427f598`), PR #3 `feature/010-review-queue` (`7c0c73d`, `38af64b`).

**Clashes and resolutions** (main wins; rows of [ADR-003-07](../decisions/ADR-003-07-align-with-main.md)):

| # | File(s) | Resolution |
|---|---|---|
| 1 | `db/migrations/versions/0002_eligibility.py` | Renamed to `0005_eligibility.py` (test to `tests/db/migrations/test_0005_eligibility.py`), after main's 0002–0004 |
| 2 | `0005_eligibility.py` `households` | Main's 0003 schema (keeps `stub_result`) + `address_state`, `seed_key`; downgrade restores 0003's schema |
| 3 | `db/seeds/generate.py` (conflict), `db/seeds/households.py` | 200 generated households; the "missing-document" household is main's `HOUSEHOLD_C`; `household_documents(dataset)` sets `stub_result` on A/B/C; `household_stub_results`, members, rule sets, applications, users and `_meta.anchor_date` are all seeded |
| 4 | `tests/db/seeds/test_reset.py` (conflict) | Both sides' tests; 200 households with A/B/C among them; stub test filters the stub-bearing docs; reseed test also clears `household_members` |
| 5 | `tests/db/test_migrations.py` (conflict) | Main's tests, version lists extended with `0005_eligibility` |

Left to the planned lane tasks (ADR-003-04, unchanged): one `Relationship`/`PayFrequency` (T002), relationship enum = main's 8 and dropping `stub_result`/`household_stub_results` (T011), real determination activity (T023), scope registry (T025).

**Checks run**
- `ruff check`: 2 E501 in the feature's WIP tests (`tests/contract/test_openapi_determinations.py:59`, `tests/integration/test_determination_journey.py:93`). Not from the merge; for the fix step.
- `ruff format --check`: 3 WIP files need formatting (`tests/contract/test_openapi_determinations.py`, `tests/integration/test_determination_traces.py`, `tests/packages/rules/test_properties.py`). Not from the merge.
- `mypy`: pass (135 files).
- `pytest -m "unit or workflow or contract"`: 679 passed, 1 failed: `test_FR_003_23_committed_openapi_has_list_case_determinations_matching_contract`, a test-first test for the route T-tasks still have to build. Not from the merge.
- `make openapi-check`: pass.
- Integration (`tests/db`, `tests/integration/test_seeded_dataset.py`): **not run**. The local MongoDB rejects this worktree's credentials (`AuthenticationFailed`). The seed output was checked directly instead: 200 unique households; A/B/C carry eligible/ineligible/cannot_determine; every demo account's household is seeded; the migration runner lists 0001–0005 in order.
- gitleaks, pip-audit: not run (the permission prompt was declined in this session).

**Needs decision:** none.
