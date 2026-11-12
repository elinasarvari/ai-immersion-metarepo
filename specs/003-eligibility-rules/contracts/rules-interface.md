# Contract: rules engine and determination activity (benefit-be)

Provider: Knowledge & data (`packages/rules`). Consumer: Workflows (`apps/worker/activities/`, BA-4). Readers of stored records: Platform & UI (API), 004, 007, 008.

## Engine

```python
# packages/rules/__init__.py
def evaluate(household: HouseholdSnapshot, as_of_date: date) -> eligibility.Determination
```
- Pure (KD-1, FR-003-08): no I/O, clock, randomness or logging. Same inputs → equal output (FR-003-04).
- Never raises for missing data; missing facts give `missing` rule results (FR-003-03).
- `rule_results` always has six entries, `ELIG-01`…`ELIG-06` in order (FR-003-05, SC-003-02).
- `StubRulesEngine` (`packages/rules/stub.py`) stays as the consumers' stub, same signature.

## Activity (unchanged signature, ADR-003-02)

```python
@activity.defn(name="determine_eligibility")
async def determine_eligibility(request: case.DeterminationRequest) -> case.Determination
```
1. Snapshot: reuse `household_snapshots[_id=uuid5(case_id,"snapshot:<as_of>")]`, else build (ADR-003-03) and insert.
2. `evaluate(snapshot, request.as_of_date)`.
3. Insert `DeterminationRecord` (`_id=uuid5(case_id,"determination:<as_of>")`); duplicate key = already done (TW-11).
4. Return the summary mapped per research R5.

All reads and writes use `Scope.for_worker(case_id, household_id)`.

## Verified facts port (ADR-003-03)

```python
class VerifiedFacts(Protocol):
    async def for_household(self, scope: Scope) -> list[VerifiedMemberFacts]: ...
```
Interim implementation reads `seeded_verifications`. 002 (pay stubs) and 005 (identity) replace it.
