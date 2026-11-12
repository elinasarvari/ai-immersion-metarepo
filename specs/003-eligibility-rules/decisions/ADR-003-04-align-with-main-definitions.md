# ADR-003-04: Reuse main's definitions; renumber the 003 migration after main's

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-06, FR-003-16, FR-003-19, SC-003-04
- **Lanes affected:** Knowledge & data, Workflows, Platform & UI (shared `packages/domain`)
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

The branch and main define the same things differently:
- Migration number: branch `db/migrations/versions/0002_eligibility.py`; main has `0002_review_queue`, `0003_case_lifecycle`, `0004_case_screens`. Both branch and main's 0003 set the `households` validator (branch adds `address_state`, `seed_key`; main adds `stub_result`).
- Enums: branch `packages/domain/household.py:11` `Relationship = Literal["self","spouse","child","other"]` and `PayFrequency`; main `packages/domain/case.py` has `Relationship` (8 values) and `PayFrequency`; branch `EligibilityResult` duplicates main's `DeterminationOutcome` (same values).
- Seed IDs: main adds `HOUSEHOLD_C` (`db/seeds/ids.py`); main's generator writes `households` with `stub_result` and `household_stub_results`.

Main wins unless that breaks 003's requirements (CLAUDE.md, integrator rule).

## Options

### Option A: 003 adapts to main
Rename the migration to `0005_eligibility`, building on main's validators (keep `0003`'s households fields except `stub_result`, which 0005 removes along with `household_stub_results`; downgrade restores them). In `packages/domain`, import `Relationship`, `PayFrequency` and `DeterminationOutcome` from `case.py` (alias `EligibilityResult = DeterminationOutcome` only if a test needs the old name). Merge main's generator into the 200-household generator; A/B/C become the demo households.
- **Pros:** one definition per concept; no edit to applied migrations (KD-11); 001 forms map directly onto snapshots.
- **Cons:** rework of branch models, the contract snapshot and migration tests.

### Option B: Keep 003's definitions, map at the boundary
- **Cons:** two `Relationship` enums with different values (a form `parent` can't be stored); violates "reuse a definition that exists"; a migration numbered 0002 twice breaks the runner.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec | yes | partial (relationship values lost) |
| Constitution and rules (VI, BA-8, KD-11) | yes | migration clash |
| Simplicity (X) | high | low |
| Security and privacy | same | same |
| Testability | contract snapshot regenerated once | mapping tests |
| Fits existing code and ADRs | yes | no |
| Reversibility | high | medium |
| Effort | medium | medium |

## Decision

We choose **Option A**. 003's models are not on main yet, so adapting them is cheap; main's are in use by 001 and 010.

## Consequences

- **Good:** consumers (004, 005, 007, 008) see one enum per concept (SC-003-04).
- **Bad / accepted trade-offs:** `tests/contract/snapshots/eligibility_models.json` is regenerated, reviewed by every lane (BA-8).
- **Work this creates:** [workflows/integrator] merge `origin/main` first; [contracts] domain reconciliation; [data] `0005_eligibility` + downgrade + tests, generator merge (users of 000 linked to A/B/C, FR-003-14), validator relationship enum = main's 8 values.

## How we verify it

CI: `tests/db/test_migrations.py` (up/down for every version in order), contract snapshot test, `ruff` and strict mypy. Compliance review: no duplicate enums in `packages/domain` (grep for `class PayFrequency`, `Relationship =`).

## References

KD-11, BA-8, constitution VI; benefit-be main `db/migrations/versions/0002_review_queue.py`, `0003_case_lifecycle.py`, `packages/domain/case.py`, `db/seeds/ids.py`.
