# Research: 001 Case lifecycle

Date: 2026-11-10. Significant decisions are ADRs in `decisions/`; these are the smaller choices. No `[NEEDS CLARIFICATION]` remained in the spec.

## R1. Verification and determination stubs
- **Decision:** `apps/worker/activities/verification.py` (`verify_documents`) and `determination.py` (`determine_eligibility`) register under the contract names (`contracts/case-workflow.md`). Until 002/003 land they return a result chosen by a test fixture or, in `make dev`, by a field on the seeded household; 002/003 replace the body with a call to their package (TW-9).
- **Rationale:** constitution VI (build against stubs); the workflow calls activities by name (TW-2), so no workflow change when the real ones land.
- **Alternatives:** stubs inside `packages/agents` / `packages/rules` (would make 001 write in other lanes' folders).

## R2. Worker repositories
- **Decision:** `apps/worker/repositories/cases.py` holds the queries for `record_case_change` (allowed by `database.md`, which lists repository modules in `apps/worker/`). It uses `packages/platform/scope.py` helpers with `Scope.for_worker` (ADR-001-06) and `packages/platform/mongo.py` for the client and transactions.
- **Alternatives:** a new `packages/cases` package (new top-level package, BA-1).

## R3. Deadline and at-risk flag
- **Decision:** `decision_deadline = received_on + 45 days` (calendar, Chicago; FR-001-01, FR-001-18). `days_remaining = deadline - case_today`, `at_risk = days_remaining <= 10` (FR-001-11), computed on read (API from the stored clock, workflow `status` query from `workflow.now()`). No action timer: 001 takes no action at the threshold. 011 adds timers for waits (TW-8). The review wait does wake at each case-clock Chicago midnight (`wait_condition(timeout=until_next_case_day(clock))`) and takes no action, so the `status` query's `days_remaining` stays current (queries see `workflow.now()` of the last workflow task; TC-44).
- **Check:** US3-1: received day 0, viewed day 36 → 9 remaining, at risk.

## R4. Coverage period
- **Decision:** pure helper `coverage_for(received_on) -> (start, end)` in `apps/worker/workflows/case_states.py`: start = first of the receipt month, end = last day of the 12th month (FR-001-22; e.g. received 2026-03-17 → 2026-03-01 to 2027-02-28). Written in the same `record_case_change` transaction as the `decided` change.

## R5. Notices
- **Decision:** `approval` (on approve) and `denial` (after `approve_denial`) are written to `outbox` with `status: requested` in the deciding transaction (US1-2, US1-3). Delivery and the denial explanation are 011. Approving the denial and its notice is one action (FR-011-06).

## R6. Override (FR-001-20)
- **Decision:** `override_to_approve` requires `reason`; the case gets `outcome: approved` and `override {reviewer_id, reason, determination_id}`; the `determinations` record is not touched (001 never writes it). Reason text is stored, never logged (PL-11).

## R7. Audit entries
- **Decision:** each applied or rejected caseworker action writes an `AuditLogEntry` (`action=caseworker_action`, `target_type=case`, outcome success/refused) in the `record_case_change` transaction. MongoDB transactions span databases on the replica set started by `make mongo-up` (`database.md`), so `benefit_audit` is included. Verify in the integration test (unverified on this cluster setup until then).

## R8. Testing approach
- **Decision:** time-skipping tests with stubbed activities (TW-13, TW-15) for every transition and signal; replay test against a recorded happy-path and override history in `tests/apps/worker/histories/` (TW-14, SC-001-05); crash test following `tests/apps/worker/workflows/test_smoke_restart.py` (TW-16, US2); integration tests for `record_case_change` idempotency and the submission guards (MongoDB + Temporal, BA-9). Test plan is the quality engineer's.

## R9. Workflow versioning
- **Decision:** `CaseWorkflow` is new, so no `workflow.patched()` now; every later change follows TW-7 and adds a replay history.

## R10. Duplicate handling of signals
- **Decision:** the workflow keeps a set of applied `request_id`s; a repeat is ignored, and `caseworker_actions._id = request_id` makes the write idempotent (FR-001-04).
