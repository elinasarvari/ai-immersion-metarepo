# ADR-003-06: How much completed history to seed before 004, 007 and 011 define their stores

- **Status:** Accepted – auto-decided
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-22, FR-003-13
- **Lanes affected:** Knowledge & data (consumers: Agents for 004, Workflows for 007/011, 008)
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

FR-003-22 asks for decided cases from 2025 and current coverage, loaded straight into the stores, with determinations, pre-written explanations, notices, review tasks and caseworker actions. On main, the stores for cases, case events, coverage periods, review tasks, caseworker actions and approval/denial outbox entries exist (`benefit-be@main:db/migrations/versions/0002_review_queue.py`, `0003_case_lifecycle.py`). There is no explanation store or model yet (004, `DecisionExplanation` is only named in specs/README.md), and the outbox validator only allows `approval` and `denial` (`0003_case_lifecycle.py`, `NOTICE_TYPES`; "011 widens this"). Also: main refuses an application when the household has coverage (`SubmissionRefusal.household_has_coverage`) or an open case, so history on demo households A/B/C would block the demo journeys. This is a scope and sequencing call across four features.

## Options

### Option A: Seed what has a store now; write the rest as test-set files
Seed decided cases (2025 and early 2026), events, determinations, snapshots, coverage periods, review tasks, caseworker actions and approval/denial outbox entries for non-demo households, in main's shapes. Write pre-written explanations and the other notice types to `db/seeds/generated/history/*.json`, keyed by `determination_id`/`case_id`; 004 and 011 load them into their stores in their own migrations/seed steps. Demo households A/B/C get no open case and no current coverage.
- **Pros:** no 003-invented shapes for other features' data; 007 and 008 work from a fresh reset for what exists.
- **Cons:** applicant history (004) and explanation checks wait for 004's loader.

### Option B: Seed everything now, defining provisional `decision_explanations` and notice shapes
- **Pros:** FR-003-22 complete in this feature.
- **Cons:** 003 defines Agents' and Workflows' contracts (VI, BA-8); likely clash at merge, settled by the integrator with "main wins".

### Option C: Defer FR-003-22 to a follow-up feature
- **Cons:** 007 and 008 known-answer metrics have no data from a fresh reset; requirement left open.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-003-22) | mostly; explanations as files | fully | no |
| Constitution and rules (VI, BA-8) | yes | defines others' contracts | yes |
| Simplicity (X) | medium | low | high |
| Security and privacy | synthetic, marked | same | n/a |
| Testability | known counts per store | same | n/a |
| Fits existing code and ADRs | main's shapes only | invents shapes | n/a |
| Reversibility | high | low | high |
| Effort | medium | high | none |

## Decision

**Option A: Seed what has a store now; write the rest as test-set files.** This is a scope question, so it goes to the option that meets the cited requirements with the least scope while staying within the constitution and rules:
- **Constitution and rules:** Option B would make 003 define `decision_explanations` (owned by 004, Agents) and widen the notice types (owned by 011, Workflows) in shared data. That breaks VI (Contracts First) and BA-8 (cross-lane data needs every lane's agreement). A and C both comply. I checked the evidence on main: `0003_case_lifecycle.py` sets `NOTICE_TYPES = ["approval", "denial"]  # 011 widens this`, and no `DecisionExplanation` model exists on main.
- **Spec:** C leaves FR-003-22 unmet, and FR-003-13 and SC-003-04 with it, because 007 and 008 would have no history after a fresh reset. A seeds every store that exists, in main's shapes. It delivers the explanations and the other notice types as deterministic files that 004 and 011 load, so SC-003-03 still holds. B fulfils more of FR-003-22 on paper, but only by breaking the rules above.
- **Fit and reversibility:** A follows the existing seed and migration pattern (KD-11, KD-13). It is easy to reverse, because the files can later be loaded or regenerated. Keeping demo households A/B/C free of open cases and current coverage stops `SubmissionRefusal.household_has_coverage` from blocking the demo journeys.

I agree with the architect's recommendation.

**Decided by:** decision-maker (automated), 2026-11-10; architect recommended Option A
**Revisit if:** 004 or 011 lands on main with its explanation store or wider notice types before 003 merges (then seed those stores directly in 003, in main's shapes), or 004/011 cannot load the generated `db/seeds/generated/history/*.json` files without reshaping them.

## Consequences

- **Good:** (A) clean ownership; 004/011 load ready-made files.
- **Bad / accepted trade-offs:** (A) FR-003-22 explanation part completes only when 004 loads the file; 004's spec must say so.
- **Work this creates:** [data] `db/seeds/history.py` (seeded IDs, main's models), files under `db/seeds/generated/history/`, tests for counts and shapes; a follow-up note to 004 and 011.

## How we verify it

Integration test after `make seed-reset`: counts per collection match the generated manifest; validators accept every document; demo households have no open case or active coverage; a schema test for the explanation file against FR-004-11's checks once 004 defines them.

## References

FR-003-22, FR-003-13, constitution VI, BA-8, KD-11, KD-13; benefit-be main `packages/domain/case.py` (`SubmissionRefusal`), `0003_case_lifecycle.py`.
