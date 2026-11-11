# workflows-lane blocked (T020-T024, T040-T042)

The benefit-be checkout is at b107708 and `origin/main` is not merged (ADR-003-04: the integrator merges it first), and the `[contracts]` tasks T001-T003 are not done. Everything in this lane depends on them:

- `packages/domain/case.py` (`Determination`, `DeterminationRequest`, `ApplicationForm`, `Relationship`, `PayFrequency`, `DeterminationOutcome`, `DenialReason`) does not exist here.
- `apps/worker/activities/determination.py` (001's stub), `repositories/stub_results.py`, `FixedStubResults` and the `main.py` wiring do not exist here, so T023 has nothing to replace.
- `packages/platform/scope.py` has no `Scope.for_worker`, and `seeded_verifications` is not in `SCOPED_HOUSEHOLD_ONLY` (T011 / platform-ui lane).
- `packages/domain/household.py` has no `VerifiedMemberFacts`, and `HouseholdSnapshot` has no `as_of_date` (T002).
- The `seeded_verifications` collection and migration 0005 (T011, T016) are missing, which TC-86 to TC-88 need.

Needed first: merge `origin/main` into `feature/003-eligibility-rules` in benefit-be, then T001, T002 (contracts), T011 (migration), and `Scope.for_worker` plus the `seeded_verifications` scope entry (platform-ui lane). Then rerun this lane.
