# Data model: 003 Eligibility rules and synthetic data

Models live in `repos/benefit-be/packages/domain/` (BA-6, BA-8). "Reused" = already on main; "branch" = already on `feature/003-eligibility-rules`, kept unless noted. All Pydantic v2, `extra="forbid"`.

## Reused from main (`packages/domain/case.py`, ADR-003-04)

`Relationship` (8 values), `PayFrequency` (weekly, biweekly, semimonthly, monthly), `DeterminationOutcome` (eligible, ineligible, cannot_determine), `DenialReason`, `Determination` (001's summary returned to the workflow; unchanged, ADR-003-02), `DeterminationRequest {case_id, household_id, as_of_date}`, `ApplicationForm`.

## `packages/domain/household.py`

| Model | Fields | Notes |
|---|---|---|
| `Job` (branch) | `job_id: UUID`, `employer`, `declared_frequency: PayFrequency`, `declared_gross: Decimal≥0` | `PayFrequency` imported from `case.py` |
| `HouseholdMember` (branch) | `member_id`, `household_id`, `given_name`, `family_name` (synthetic), `date_of_birth`, `relationship: Relationship`, `address_state`, `citizenship_attested: bool\|None`, `medicare_entitled: bool\|None`, `declared_zero_income`, `jobs`, `coverage_year` | stored in `household_members`, one per member per year (R7) |
| `PayStubFact` (branch) | `document_id`, `pay_date`, `frequency`, `gross_pay` | verified values only |
| `JobIncome` (branch) | `job_id`, `stubs: list[PayStubFact]` | empty = no usable stub → missing |
| `MemberFacts` (branch) | `member_id`, `relationship`, `date_of_birth`, `address_state`, `citizenship_attested`, `medicare_entitled`, `identity_verified: bool\|None`, `declared_zero_income`, `jobs: list[JobIncome]` | no names (VIII) |
| `HouseholdSnapshot` (branch) | `snapshot_id`, `household_id`, `case_id`, `as_of_date` (**new**), `captured_at`, `members` | engine input; size = `len(members)`; `_id = uuid5(case_id, "snapshot:<as_of>")` |
| `VerifiedMemberFacts` (**new**, ADR-003-03) | `household_id`, `member_id`, `identity_verified: bool\|None`, `jobs: list[JobIncome]` | output of the `VerifiedFacts` port; interim store `seeded_verifications` |

## `packages/domain/eligibility.py`

| Model | Fields | Notes |
|---|---|---|
| `RuleId` (branch) | `ELIG-01`…`ELIG-06` | FR-003-01 order |
| `RuleOutcome` (branch) | pass, fail, missing | |
| `EligibilityResult` | **removed**; use `DeterminationOutcome` (ADR-003-04) | |
| `PovertyGuideline`, `RuleSet` (branch) | as built | ADR-003-01 |
| `MissingItem` (branch) | `item`, `member_id?`, `job_id?`, `reason` | `item` codes: `applicant`, `rule_set`, `citizenship_attested`, `identity_verified`, `medicare_entitled`, `pay_stub` |
| `RuleResult` (branch) | `rule_id`, `outcome`, `inputs: dict[str,str]`, `threshold: str\|None`, `policy_ref`, `missing` | FR-003-05 |
| `Determination` (branch, engine output) | `result: DeterminationOutcome`, `as_of_date`, `rule_set_id?`, `rule_set_version?`, `engine_version`, `household_size`, `household_monthly_income?`, `monthly_income_limit?`, `rule_results`, `missing_items` | pure output of `evaluate` |
| `DeterminationRecord` (branch) | `determination_id`, `household_id`, `case_id`, `snapshot_id`, `recorded_at`, `determination` | stored in `determinations`, `_id = determination_id` |
| `DeterminationView` (**new**, API) | `determination_id`, `result`, `reason_code: DenialReason\|None`, `as_of_date`, `rule_set_id`, `rule_set_version`, `household_size`, `household_monthly_income`, `monthly_income_limit`, `rules: list[RuleResult]`, `missing_items`, `recorded_at` | see `contracts/rest-api.openapi.yaml` |

## Collections (migration `0005_eligibility`, ADR-003-04)

| Collection | Scope | Change |
|---|---|---|
| `households` | user scope only | validator = main's 0003 fields + `address_state`, `seed_key`, minus `stub_result` (the merge kept `stub_result` on A/B/C until T023, ADR-003-07); 200 households, demo A/B/C among them |
| `household_members` | household-only | strict validator (branch), relationship enum = main's 8; index `household_year` |
| `household_snapshots` | case | strict validator, adds `as_of_date`; unique `(case_id, as_of_date)` |
| `determinations` | case | strict validator; index `(case_id, recorded_at desc)` |
| `rule_sets` | unscoped | strict validator; unique `(rule_set_id, version)` |
| `seeded_verifications` | household-only (**new**, add to `SCOPED_HOUSEHOLD_ONLY`) | unique `(household_id, member_id)`; temporary (ADR-003-03) |
| `household_stub_results` | — | **dropped** (downgrade recreates it) |
| `_meta` | unscoped | adds `anchor_date` |

## Generated test sets (`db/seeds/generated/`, BA-11)

`known_answers.json` (≥30, FR-003-09), `pay_stub_extractions.json` (10–20, 002), `redeterminations_due.json` (007), `expected_metrics.json` (008), `history/*.json` (ADR-003-06), `manifest.json` (seed, generator version, file hashes for SC-003-03). Field sets as pinned by `tests/integration/test_seeded_dataset.py:23`.

## State

Determinations are immutable: one per `(case_id, as_of_date)`. A redetermination is a new case and so a new determination.
