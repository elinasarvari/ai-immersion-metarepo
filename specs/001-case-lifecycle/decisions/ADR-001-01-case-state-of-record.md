# ADR-001-01: CaseWorkflow owns the state; MongoDB holds an idempotent projection

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-02, FR-001-03, FR-001-04, FR-001-10, SC-001-01, SC-001-05
- **Lanes affected:** Workflows | Knowledge & data
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

A case has two homes: the durable `CaseWorkflow` (constitution II, TW-3) and the `cases` / `case_events` collections that 006, 008 and 010 read (specs/README.md "MongoDB"; `repos/benefit-be/db/migrations/versions/0001_baseline.py:35` creates them with a minimal validator). Exactly one must decide transitions, or a restart can leave them disagreeing (FR-001-03). Workflow code may not touch the DB (TW-1, TW-2), and Temporal may run an activity more than once (TW-11), so every write must tolerate a retry without a second history entry, notice or task (FR-001-04, SC-001-01). The API may read the case only from MongoDB or a query (PL-2, BA-5).

## Options

### Option A: Workflow decides, activities project every change idempotently
`apps/worker/workflows/case.py` holds the state machine (pure transition table in `case_states.py`). Each change calls one activity, `record_case_change`, with a sequence number `seq` and IDs the workflow generated with `workflow.uuid4()` (replay-stable, TW-1). The activity writes the `cases` update and the `case_events` insert in one transaction (KD-10); a unique index on `case_events (case_id, seq)` turns a retried insert into a no-op. Notices go to `outbox` with `_id = uuid5(case_id, notice_type)`; review tasks use a workflow-generated `_id`.
- **Pros:** one authority; retries safe by construction; readers never call Temporal for lists; history survives in Mongo for 008.
- **Cons:** the projection lags the workflow by one activity; two writes per transition.

### Option B: MongoDB is the authority; the workflow reads state from an activity
Each step loads the case document, checks the transition there and writes it back.
- **Pros:** one document is "the truth" for readers.
- **Cons:** state lives outside the replayable history, so a restart can diverge (II); every decision becomes an I/O round trip; optimistic locking needed.

### Option C: Workflow only; readers use Temporal queries
No projection; the API queries the workflow for state and history.
- **Pros:** no duplicate data.
- **Cons:** lists and metrics (006, 008) can't query across workflows; closed workflows age out of retention; history in workflow memory grows with the case.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-001-02/03/04/10) | Yes | Restart risk | No cross-case reads |
| Constitution and rules (II, TW-1/2/11, KD-10) | Yes | Strains II | Yes |
| Simplicity (X) | Medium | Medium | High, until 006/008 |
| Security and privacy | Repository scope applies | Same | Query bypasses repository scope |
| Testability | Stubbed activity in time-skipping tests | Needs DB in workflow tests | Easy |
| Fits existing code and ADRs | Smoke workflow pattern (`apps/worker/workflows/smoke.py:20`) | – | – |
| Reversibility | High | Low | Medium |
| Effort | 1 activity + 1 migration | Higher | Lowest now, rework later |

## Decision

We choose **Option A**: the workflow is the only place a transition is decided, and MongoDB is a projection written by one idempotent activity per change. It is the only option that keeps II and serves cross-case readers; idempotency comes from workflow-generated keys plus unique indexes, not from checks in code.

## Consequences

- **Good:** restart and replay tests cover all decision logic; duplicates are refused by the database.
- **Bad / accepted trade-offs:** readers can see the previous state for the duration of one activity; the live `CaseStatus` query (contracts/case-workflow.md) covers the console's detail view if that matters.
- **Work this creates:** Workflows: `case.py`, `case_states.py`, `record_case_change`, `request_notice`, `open_review_task` activities. Knowledge & data: migration `0002_case_lifecycle` (validators, `case_events (case_id, seq)` unique, `outbox` deterministic `_id`). Contracts: `Case`, `CaseEvent`, `CaseChange` models.

## How we verify it

Workflow test with an activity stub that is called twice for the same `seq` (CI); integration test that runs `record_case_change` twice and finds one event (CI); restart test (TW-16) and replay test (TW-14) on the recorded happy-path history (CI); compliance review checks no workflow module imports `db/` or `pymongo` (TW-2).

## References

Constitution II, VI; TW-1, TW-2, TW-3, TW-11, TW-14, TW-16; KD-10, KD-11; `database.md`; specs/000 research R16.
