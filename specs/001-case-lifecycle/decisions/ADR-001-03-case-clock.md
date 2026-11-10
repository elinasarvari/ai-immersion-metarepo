# ADR-001-03: Case clock as parameters on the case, computed from workflow time

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-01, FR-001-11, FR-001-13, FR-001-18, FR-001-22; FR-011-04, FR-011-05 (consumers)
- **Lanes affected:** Workflows | Platform & UI
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

FR-001-13 requires every case date (deadline, as-of date, decision date, history) to come from a per-case clock: the real date outside the demo profile, one day per minute in it, with jumps when a supervisor fires a timer early (FR-011-04, FR-011-05, owned by 011). Workflow code may only use `workflow.now()` and may not read settings (TW-1); deadlines must be Temporal timers (TW-8). The API also needs "case-clock now" to show days remaining (FR-001-11). `packages/platform/clock.py:36` already computes Chicago calendar days (FR-001-18), and `apps/worker/workflows/calendar.py` wraps it for workflow code. `Settings.DEMO_PROFILE` exists (`packages/platform/settings.py:66`).

## Options

### Option A: Clock parameters stored with the case, one pure function
`CaseClock {real_start, case_start, scale, offset}` (domain model) is fixed when the case opens (scale 1 or 1440 from `DEMO_PROFILE`), passed in `CaseStart`, and stored on the case document. `case_now(clock, real_now) = case_start + (real_now - real_start) * scale + offset` lives in `packages/platform/clock.py`; the workflow calls it with `workflow.now()`, the API with `SystemClock`. 011 adds `offset` changes through its advance-clock signal. Timers sleep `case_delta / scale` real time.
- **Pros:** deterministic; workflow and API compute the same date; 011 extends without a contract change.
- **Cons:** a clock change (offset) must be written to the case document as well as held in the workflow.

### Option B: Clock as a separate service or activity
An activity returns case-clock now on each use.
- **Pros:** one implementation.
- **Cons:** an activity per date read; results enter history; overkill (X).

### Option C: Real time only, scale timers in settings
- **Pros:** simplest.
- **Cons:** breaks FR-001-13 (dates in the demo would not follow the scale).

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-001-13) | Yes | Yes | No |
| Constitution and rules (TW-1, TW-8) | Yes | Yes | Yes |
| Simplicity (X) | High | Low | Highest |
| Testability | Pure function + time skipping | Stub needed | Easy |
| Fits existing code | Extends `clock.py`, `calendar.py` | New activity | – |
| Reversibility | High | Medium | – |

## Decision

We choose **Option A**: one pure function and parameters fixed at opening make the case clock deterministic in the workflow and reproducible in the API, and 011 only changes `offset`.

## Consequences

- **Good:** history entries record `case_time` and `real_time` from one call (FR-001-13 edge case); deadline = Chicago date of `case_now` at receipt + 45 calendar days.
- **Bad / accepted trade-offs:** `scale` is fixed per case; switching profile mid-case does not rescale existing cases (accepted: the demo resets data).
- **Work this creates:** Platform & UI: `case_now`, `case_today` in `packages/platform/clock.py`. Workflows: `calendar.py` wrapper. Contracts: `CaseClock` model.

## How we verify it

Unit tests on `case_now` with scale 1 and 1440 (CI); time-skipping workflow test proving the deadline and history dates use the case clock (CI); the FR-001-11 test computes 9 days remaining from a fixed clock.

## References

FR-001-13, FR-011-04; TW-1, TW-8; specs/000 research R21 (time zone).
