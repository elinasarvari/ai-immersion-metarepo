# ADR-010-05: Which review reason a failed determination uses

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-01, FR-010-03, US2 scenario 2
- **Lanes affected:** Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

FR-010-01 lists six reasons and says every task MUST have one. "Retry limit reached" is named only under Verification review. FR-010-03 and US2 scenario 2 require a task when **determination** fails 3 times but don't name its reason. Verification review's actions end in "Determining", so they don't fit a determination failure; the table can't grow without changing the spec (SC-010-01 counts six reasons). This is a requirements interpretation, so it's the team's call.

## Options

### Option A: Cannot determine, with cause `determination_failed`
Actions: Request information; Correct a value* → determined again.
- **Pros:** keeps six reasons; "Correct a value → determined again" is a natural retry path.
- **Cons:** "Cannot determine" is also a rules *result*; the evidence `cause` must distinguish the two.

### Option B: A seventh reason, "Determination failed"
Actions: Retry determination; Correct a value*.
- **Pros:** clearest for caseworkers.
- **Cons:** spec change (FR-010-01, SC-010-01) and a contract change consumed by 006 and 008.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec as written | Yes | Needs spec edit |
| Constitution and rules | I, IV | I, IV |
| Simplicity (X) | High | Medium |
| Security and privacy | Same | Same |
| Testability | Same | Same |
| Fits existing code and ADRs | ADR-010-02 table unchanged | Table grows |
| Reversibility | High | Medium |
| Effort | Low | Medium |

## Decision

**Option A: "Cannot determine", with cause `determination_failed`.** When determination fails after its retry limit (ADR-010-04), the review task carries the existing "Cannot determine" reason and the evidence cause `determination_failed`, which tells it apart from a rules-engine "Cannot determine" result. Its actions are Request information and Correct a value (the case is determined again). The six reasons in FR-010-01 and SC-010-01 stay as they are, so there is no spec or contract change. The choice stays behind one constant in `apps/worker/workflows/review.py` (`DETERMINATION_FAILURE_CAUSE`).

Decided by Aniket Rane, 2026-11-10.

## Consequences

- **Good:** either answer is a one-constant change in the workflow plus, for B, a contracts PR.
- **Bad / accepted trade-offs:** under A, 006 should show the cause so caseworkers know rules didn't run.
- **Work this creates:** [workflows] constant and test; under B also [contracts] new `ReviewReason` and spec edit by the spec owner.

## How we verify it

Workflow test `test_FR_010_03_determination_retry_limit_creates_review_task` asserts the chosen reason and cause.

## References

FR-010-01, FR-010-03, SC-010-01; ADR-010-02, ADR-010-04.
