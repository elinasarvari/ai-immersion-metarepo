# ADR-010-06: How "open for 2 days" and "4 days" are counted

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-02, FR-001-18, SC-010-03
- **Lanes affected:** Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

FR-010-02 says "not actioned within 2 days" and "after 4 days". FR-001-18 says all day counts use calendar days, and the platform computes day counts in America/Chicago (`benefit-be:packages/platform/clock.py:32-41`, database.md). "2 days" can mean 48 elapsed case-clock hours, or the start of the 2nd Chicago calendar day after opening. A task opened at 23:00 gets its reminder ~47 hours apart under the two readings. In the demo profile (one day per minute, FR-011-04) the difference is under a minute. This is a policy reading of the spec, so the team decides.

## Options

### Option A: Elapsed case-clock time (48 h / 96 h)
Due = `opened_at + days × 24 h` on the case clock.
- **Pros:** simplest timer; identical behaviour in both profiles; easy to test.
- **Cons:** reminders can land at night.

### Option B: Chicago calendar days (midnight boundaries)
Due = local midnight starting day `opened_date + days`.
- **Pros:** matches how 45-day deadlines are counted with `days_between`.
- **Cons:** a task opened at 23:59 is "1 day old" a minute later; DST handling in the due-time helper.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (FR-010-02) | Yes | Yes |
| Constitution and rules (FR-001-18) | Calendar, not business days | Calendar days |
| Simplicity (X) | High | Medium |
| Security and privacy | Same | Same |
| Testability | Simple | DST cases needed |
| Fits existing code | `workflow.now()` arithmetic | `calendar.py` helpers |
| Reversibility | High | High |
| Effort | Low | Low |

## Decision

**Option A: elapsed case-clock time.** The reminder is due `opened_at + 2 × 24 h` and the escalation `opened_at + 4 × 24 h` on the case clock. FR-001-18 is read as "calendar, not business, days", which A satisfies; it is the simplest timer and behaves the same in both clock profiles. The rule stays isolated in `review_timers.due_at()` (ADR-010-03).

Decided by Aniket Rane, 2026-11-10.

## Consequences

- **Good:** one function changes either way.
- **Bad / accepted trade-offs:** under A the queue's "days open" shown by 006 should use the same rule to avoid off-by-one confusion.
- **Work this creates:** [workflows] `due_at()` and its tests.

## How we verify it

Unit tests of `due_at()` at 00:01, 23:59 and across a DST change; time-skipping test for SC-010-03.

## References

FR-010-02, FR-001-18, FR-011-04, SC-010-03; database.md (America/Chicago); ADR-010-03.
