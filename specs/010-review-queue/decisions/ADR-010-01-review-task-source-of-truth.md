# ADR-010-01: CaseWorkflow owns review tasks; `review_tasks` is a projection written by activities

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-01, FR-010-02, FR-010-03, FR-001-07
- **Lanes affected:** Workflows | Knowledge & data | Platform & UI
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

A review task is a durable human wait (constitution II, TW-4) inside one `CaseWorkflow` per case (TW-3). The shared queue (006, FR-006-01) must list open tasks across all cases, sorted by decision deadline, with reminder and escalation flags. The baseline already creates `review_tasks` and `caseworker_actions` with minimal validators that the owning feature tightens (`benefit-be:db/migrations/versions/0001_baseline.py:1-5,35-48,152-156`). The Explanation review reason "does not block the decision" (FR-010-01), so one case can have more than one open task, and a task can still be open when the case is Decided. No `CaseWorkflow` exists yet (`benefit-be:apps/worker/workflows/` holds only `smoke.py` and `calendar.py`); 001 has no plan yet.

## Options

### Option A: Workflow state is authoritative, MongoDB holds a projection
`CaseWorkflow` keeps `open_tasks: dict[UUID, ReviewTaskState]`. Opening, flagging and closing a task each call an idempotent activity (`upsert_review_task`) that writes `review_tasks` keyed by a task ID made with `workflow.uuid4()` (TW-1). The API reads the collection for the queue; the workflow never reads it back.
- **Pros:** one durable owner; the queue is a plain indexed query (database.md); no Temporal visibility setup.
- **Cons:** the projection can lag the workflow by one activity; two writers must not exist (enforced by ownership).

### Option B: Queue served from Temporal (queries plus search attributes)
The API lists cases by a custom search attribute `HasOpenReview` and queries each workflow for its tasks.
- **Pros:** no projection to keep in step.
- **Cons:** N queries per queue page; sorting by deadline and filtering by flags needs several custom search attributes on the dev server; the reporting store (008) can't export it; PL-2 allows queries but this makes the queue depend on worker uptime.

### Option C: MongoDB authoritative, workflow polls
Tasks live only in MongoDB; the workflow polls with an activity until closed.
- **Cons:** breaks TW-4 (wait on signal, not polling) and constitution II.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-010-01/02/03, FR-006-01) | Yes | Yes, slower | Yes |
| Constitution and rules | II, TW-4/5/11 | II, PL-2 | Breaks TW-4 |
| Simplicity (X) | High | Low | Medium |
| Security and privacy | Household filter in repository (VIII) | Needs per-case auth on each query | Same as A |
| Testability | Time-skipping + fake repository | Needs visibility in tests | Polling timers |
| Fits existing code | Baseline collections exist | New search attributes | – |
| Reversibility | High | Medium | – |
| Effort | Low | High | Medium |

## Decision

We choose **Option A**. It keeps the workflow the single source of truth required by TW-4/TW-5 and gives 006 and 008 a normal indexed collection. `CaseWorkflow` does not complete while any task in `open_tasks` is open, so a non-blocking Explanation review can still be closed after the case is Decided.

## Consequences

- **Good:** queue reads never touch Temporal; history stays small because evidence is stored by reference (`evidence_refs`), not inline.
- **Bad / accepted trade-offs:** projection lag of one activity; the API must treat `status` as advisory and let the workflow refuse (ADR-010-02).
- **Work this creates:**
  - [contracts] `packages/domain/review.py`: `ReviewReason`, `ReviewTask`, `ReviewTaskState` (data-model.md).
  - [workflows] `apps/worker/activities/review_tasks.py` (`upsert_review_task`, `set_review_flag`, `close_review_task`) and `apps/worker/repositories/review_tasks.py`; `CaseWorkflow` keeps `open_tasks` and waits until none block.
  - [data] migration `0002_review_queue`: tightened `$jsonSchema` for `review_tasks`, `caseworker_actions`; indexes in data-model.md.

## How we verify it

- Workflow test (TW-13): open two tasks (Adverse determination + Explanation review), close the blocking one, assert the case decides and the workflow stays running until the second is closed.
- Integration test: replaying `upsert_review_task` with the same task ID leaves one document (TW-11).
- Code reviewer: no code outside `apps/worker/` writes `review_tasks` (CI grep for `review_tasks` writes in `apps/api/`).

## References

TW-1, TW-3, TW-4, TW-5, TW-11, PL-2, BA-8, database.md, constitution II, VI, VIII; FR-001-07, FR-006-01.
