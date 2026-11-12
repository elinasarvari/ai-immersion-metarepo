# ADR-003-03: Snapshot capture in the worker, with seeded verifications until 002 and 005 land

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-14, FR-003-16, FR-003-17, FR-003-19, FR-003-03
- **Lanes affected:** Knowledge & data, Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

Evaluation takes a household snapshot captured for the case (FR-003-19). Attested facts are seeded for seeded households and come from the form for new ones (FR-003-16); identity and income come from verification (005, 002), neither of which is on main. Today the demo journeys rely on 001's per-household stub results (`benefit-be@main:db/seeds/generate.py`, `STUB_RESULTS`: A eligible, B ineligible, C cannot determine), and every e2e journey submits the same zero-income form (`benefit-fe@main:e2e/support/cases.ts`, `validForm`). The worker scope may read household-only collections by `household_id` and case collections by `case_id`, but not `households` (`benefit-be@main:packages/platform/scope.py`, `_worker_limit`; ADR-001-06 cited in `apps/worker/repositories/stub_results.py:3`). 001's migration says "003 drops" `household_stub_results` (`0003_case_lifecycle.py`).

## Options

### Option A: Seeded household → seeded members + seeded verifications; new household → form, unverified
The activity reads, under `Scope.for_worker`: an existing `household_snapshots` record for `snapshot_id` (reuse it, never recapture); else `household_members` for the as-of year; if none, the case's `applications` form (research R8). Verified facts come through a `VerifiedFacts` port; its interim implementation reads a new household-only collection `seeded_verifications` (per member: `identity_verified`; per job: verified pay stub facts). It replaces `household_stub_results`, which this feature drops. 002/005 later swap the port's implementation. Demo households A/B/C are seeded so the real engine gives Eligible / Ineligible (income over limit) / Cannot determine (declared job, no usable stub) (FR-003-14).
- **Pros:** spec-faithful (seeded facts for seeded households); demo journeys keep their outcomes from real rules; same pattern as ADR-001-06; clean seam for 002/005.
- **Cons:** a temporary collection; the form's facts are ignored for seeded households (as FR-003-16 says).

### Option B: Always build from the form; leave identity and income missing until 002/005
- **Pros:** no interim collection.
- **Cons:** every demo case becomes Cannot determine; breaks the main e2e journeys `apply-for-coverage`, `caseworker-approves-denial` and the demo story.

### Option C: Keep 001's stub outcome until 002 lands
- **Cons:** violates constitution I and FR-003-01 (outcome not from rules); leaves FR-003-23 showing fake traces.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-003-16/17/19) | yes | yes, but demo empty | no |
| Constitution and rules (I, VIII, KD-9) | yes | yes | violates I |
| Simplicity (X) | medium | high | high |
| Security and privacy | household-only scope filter | same | same |
| Testability | port with fake | simple | n/a |
| Fits existing code and ADRs | mirrors ADR-001-06 | breaks main's e2e | stub stays |
| Reversibility | high (swap port) | high | n/a |
| Effort | medium | low | none |

## Decision

We choose **Option A**: it is the only option that keeps rules deciding (I) and the main e2e journeys meaningful before 002/005 land, and it reuses the precedent for worker-readable seeded data. The snapshot is written once per `(case_id, as_of_date)` and reused, so later household changes never alter a determination (FR-003-19).

## Consequences

- **Good:** 002 and 005 plug in by implementing `VerifiedFacts`; nothing else changes.
- **Bad / accepted trade-offs:** `seeded_verifications` is temporary and must be removed by 002/005 (each removes its part).
- **Work this creates:** [contracts] `VerifiedMemberFacts` model in `packages/domain/household.py`; [data] migration creates `seeded_verifications` (household-only, validator, unique `(household_id, member_id)`), drops `household_stub_results` and the `households.stub_result` field, and adds the name to the scope registry (`packages/platform/scope.py` is Platform-owned: separate commit); seeds for demo households A/B/C; [workflows] `apps/worker/repositories/snapshots.py`, `verified_facts.py`, snapshot capture inside `determine_eligibility`, delete `stub_results.py` and the `FixedStubResults` stub; [platform-ui] update e2e comments that say "stub result".

## How we verify it

Activity test: same case twice → one snapshot, reused; member change after capture does not change the determination. Integration test (local MongoDB + Temporal): seeded A/B/C submit `validForm` → Eligible / Ineligible / Cannot determine. The main e2e suite passes (CI). Scope test: worker cannot read `seeded_verifications` of another household.

## References

FR-003-14, FR-003-16, FR-003-17, FR-003-19; constitution I, VIII; KD-9, KD-10; TW-11; ADR-001-06 (benefit-be main); `packages/platform/scope.py`.
