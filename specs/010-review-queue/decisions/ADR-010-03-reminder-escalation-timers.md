# ADR-010-03: Reminder and escalation are per-task Temporal timers on the case clock

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-02, FR-011-04, FR-011-05, FR-007-04
- **Lanes affected:** Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

A task open 2 days gets a "reminder" flag; 4 days, or the coverage end date passing during an open redetermination review, gets "escalated" (FR-010-02). Waits run on the case clock (FR-001-13) and follow the demo scale of one day per minute; a supervisor can fire the next timer early and the clock jumps (FR-011-04, FR-011-05). TW-8 requires deadlines to be Temporal timers. The edge case "action at the moment the reminder fires: the action wins" must hold. The case-clock mechanism and the advance-clock signal belong to 011 and 001 and are not built yet.

## Options

### Option A: Timers inside CaseWorkflow
For each open task the workflow computes case-clock due times (`opened_at + REVIEW_REMINDER_DAYS`, `+ REVIEW_ESCALATION_DAYS`, `coverage_end` when present) and converts them to real durations through the case-clock helper (011). The main loop waits with `workflow.wait_condition(..., timeout=<nearest due>)`; on wake it processes queued actions **first**, then sets due flags only on tasks still open, via `set_review_flag` (conditional update on `status: open`).
- **Pros:** TW-8 and TW-13 time-skipping tests; the advance-clock signal just wakes the loop; action-wins ordering is deterministic.
- **Cons:** depends on 011's case-clock helper (stubbed until then).

### Option B: Temporal Schedule sweeper
A schedule runs every N minutes, finds overdue `review_tasks` in MongoDB and sets flags.
- **Cons:** the demo jump (FR-011-05) is invisible until the next sweep; breaks TW-8 (deadline not a workflow timer); a second writer to `review_tasks` (against ADR-010-01).

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (FR-010-02, FR-011-05) | Yes | Delayed flags |
| Constitution and rules | II, TW-4, TW-8 | Against TW-8 |
| Simplicity (X) | Medium | Medium |
| Security and privacy | Same | Same |
| Testability | Time-skipping | Real clock |
| Fits existing code and ADRs | ADR-010-01 | Conflicts ADR-010-01 |
| Reversibility | High | High |
| Effort | Low–medium | Medium |

## Decision

We choose **Option A**: it is the only option that honours TW-8 and the demo clock jump. Wait lengths are settings (`REVIEW_REMINDER_DAYS=2`, `REVIEW_ESCALATION_DAYS=4`, FR-011-04) passed into the workflow at start, never read inside it (TW-1). How "2 days" is counted is open in ADR-010-06; the timer code takes the due-time function as one helper so either answer is a one-line change.

## Consequences

- **Good:** flags appear on the same tick as the timer in both profiles.
- **Bad / accepted trade-offs:** 010's workflow tests need 011's case-clock stub; changing the waits for running workflows needs `workflow.patched()` (TW-7).
- **Work this creates:**
  - [contracts] settings `REVIEW_REMINDER_DAYS`, `REVIEW_ESCALATION_DAYS` in `.env.example` (Platform & UI owns settings); `ReviewFlag` enum.
  - [workflows] `apps/worker/workflows/review_timers.py` (pure due-time functions), loop integration, `set_review_flag` activity.

## How we verify it

- Time-skipping tests: +2 days → reminder; +4 days → escalated; coverage end passes → escalated (FR-010-02).
- Test: signal an action and let the reminder timer fire in the same workflow task → task closed, no reminder flag.
- Replay test with a recorded history (TW-14).

## References

TW-1, TW-7, TW-8, TW-13, TW-14; constitution II; FR-001-13, FR-011-04, FR-011-05, FR-007-04; ADR-010-01, ADR-010-06.
