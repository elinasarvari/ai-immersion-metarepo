# Fixes: workflows lane (T020–T024, T040–T042)

Understood first: `verify.md` listed no failing worker test; the workflows lane was "blocked" until
`origin/main` was merged and contracts landed (`lanes/workflows-lane/blocked.md`). The merge is in,
so the lane's tasks were built. Each entry: check, proof, why it failed, change.

- **TC-86–TC-88** (`tests/integration/worker/test_worker_stores.py`): FR-003-16, -19, -04; ADR-003-02, -03; TW-11.
  Missing: no `VerifiedFacts` port, snapshot store or determination store existed.
  Added `apps/worker/repositories/{verified_facts,snapshots,determinations}.py` (all through `Scope.for_worker`;
  a duplicate key counts as done). **environment:** the integration tests were written but not run here:
  the local MongoDB rejects this worktree's credentials (`OperationFailure` in `reset_stores`) and another stack
  holds the ports. They also need `seeded_verifications` (data lane's migration 0005/T011) and
  `as_of_date` in the snapshot validator. The stored `seeded_verifications` documents are read as
  `{household_id, member_id, identity_verified, jobs[{job_id, stubs[]}]}` (= `VerifiedMemberFacts`).
- **TC-89–TC-94** (`tests/apps/worker/activities/test_snapshot.py`): FR-003-16, -17, -19, -03, -21; R7, R8.
  Missing: no capture step. Added `apps/worker/activities/snapshot.py` (`SnapshotCapture`: reuse by
  `(case_id, as_of_date)`, else members of the as-of year, else the form; merge verified facts; no names).
- **TC-95–TC-98** (`tests/apps/worker/activities/test_determination.py`): FR-003-02, -04, -19; ADR-003-02; R5, R6.
  The activity was 001's stub. Replaced its body with capture, `evaluate`, idempotent insert of
  `DeterminationRecord` (`_id = determination_id`) and the R5 summary; signature unchanged. Deleted
  `repositories/stub_results.py`, `FixedStubResults` and their tests (T023, ADR-003-03); `main.py` wires the real
  stores (`determination_activities`); `tests/integration/case_stack.py` now uses the real activity.
  The old `test_FR_001_16_stub_*` tests asserted the removed stub; their requirement is now covered by TC-95/97
  and the A/B/C journey (TC-129).
- **TC-99** (`tests/apps/worker/workflows/test_determination_failures.py`): FR-003-02, TW-10, ADR-001-02.
  The test plan says the case "opens review" after the store fails past its retries, but Accepted ADR-001-02
  (main) runs `determine_eligibility` with UNTIL_DONE (retried until the store answers) and ADR-003-02 forbids a
  workflow change, so no failure path can open a review. The test follows the ADRs: the store fails 5 times
  (past RULES_STEP's 3), the case is neither failed nor left in `determining` once the store answers, and the
  ineligible household opens an adverse-determination review. Open question for the PR: amend TC-99's wording.
- **TC-100/TC-101** replay tests (`test_case_replay`, `test_review_replay`): pass unchanged (workflow untouched).
- `make check` pieces run here: `ruff check`/`format` clean on my files; `mypy` clean for `apps/worker` and
  worker tests (one error remains in `db/seeds/households.py`, data lane); `pytest tests/apps/worker -m "not integration"`: 242 passed.
- **T032** left open: its journey (`test_determination_journey.py`) needs MongoDB, Temporal and the data and
  platform-ui lanes' pieces; it could not run here (environment: Mongo credentials, ports in use).
