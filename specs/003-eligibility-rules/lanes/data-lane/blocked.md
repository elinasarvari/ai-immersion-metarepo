# data-lane blocked

`benefit-be` on this branch does not yet contain `origin/main` (it has 0001/0002 migrations only; main has 0003–0004, the new `case.py` models, `db/seeds/generate.py` and `users.py`). The integrator merges main first (ADR-003-04), and contracts T001–T002 have not landed (`EligibilityResult` and the snapshot without `as_of_date` still exist). The tasks below build on main's migrations, case shapes and users, so writing them now would be redone after the merge.

Not done, to be run in a later pass after the merge and T001/T002:

- T036/T011: `tests/db/migrations/test_0005_eligibility.py` (TC-72–74) and `0005_eligibility.py` (needs main's 0003 `households` validator and 0004).
- T037/T012/T015/T016: A/B/C demo households through `evaluate`, linking 000's demo users (main's `users.py`), `db/seeds/verifications.py` (TC-56, 75–77).
- T038/T017/T018: `test_sets.py`, `history.py` (history uses main's case, event, outbox, coverage shapes) (TC-78–80, 82, 84).
- T019: seeded-dataset tests (TC-81, 83, 85).

Also, outside this lane: T010's change to `stub.py` still imports `EligibilityResult`; the contracts lane's T001 must switch it to `DeterminationOutcome` (same for `engine.py`, `checks.py`, and the tests that import it).
