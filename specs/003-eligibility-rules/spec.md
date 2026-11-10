# Feature Specification: Eligibility Rules and Synthetic Data

**Feature Branch**: `feature/003-eligibility-rules`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Deterministic Medicaid eligibility rules engine and synthetic data set"

## Lane & Dependencies

- **Lane**: Knowledge & data
- **Provides**: determinations with explanation traces for any household and as-of date; the
  synthetic data set and test sets every lane uses; the determination section on the case
  page. Used by 001, 002, 004, 007, 008 and 011.
- **Depends on**: 000 (configuration). The rules engine depends on nothing else and must work
  standalone; only the determination section needs 001's case page.
- **Out of scope**: eligibility groups other than adults 19–64 on income; disability, long-term
  care and spend-down rules; other programs; real personal data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decide eligibility deterministically (Priority: P1)

Given a household's verified information and a date, the system decides whether the applicant
qualifies for Medicaid for adults 19–64, the same way every time.

**Why this priority**: Decisions must be reproducible and auditable; AI never decides.

**Independent Test**: Run the known-answer cases and confirm every result matches, on repeated
runs.

**Acceptance Scenarios**:

1. **Given** a household meeting every rule, **When** it is evaluated, **Then** the result is
   "Eligible".
2. **Given** a household failing any rule, **When** it is evaluated, **Then** the result is
   "Ineligible" and names every rule that failed.
3. **Given** a household missing information a rule needs, **When** it is evaluated, **Then** the
   result is "Cannot determine" and lists what is missing, never "Ineligible".
4. **Given** the same household and date, **When** it is evaluated twice, **Then** both results
   are identical.

---

### User Story 2 - Explain every decision (Priority: P1)

Each decision comes with an explanation: every rule applied, the values used, the threshold and
the policy reference.

**Why this priority**: Caseworkers and applicants must understand why.

**Independent Test**: Evaluate a known case and check the explanation lists each rule with
inputs, threshold, outcome and policy reference.

**Acceptance Scenarios**:

1. **Given** an income-ineligible household, **When** it is evaluated, **Then** the explanation
   shows household income, household size, the income limit used, the program year and the
   policy reference.

---

### User Story 3 - Replay a past decision (Priority: P2)

A past decision can be recomputed under the rules in force on its original date.

**Why this priority**: Needed for applicant history and audit.

**Independent Test**: Evaluate the same household as of last year and this year and confirm the
income limits for each year are used.

**Acceptance Scenarios**:

1. **Given** rule sets for two program years, **When** a household is evaluated as of a date in
   the earlier year, **Then** the earlier year's limits are used.

---

### User Story 4 - Shared synthetic data set (Priority: P2)

Every team member loads the same realistic, clearly synthetic data set, including the test sets
other features need.

**Why this priority**: All lanes build and test against this data; its edge cases are the
known-answer tests.

**Independent Test**: Generate the data set twice with the same seed and confirm identical output.

**Acceptance Scenarios**:

1. **Given** the fixed seed, **When** the data set is generated on two laptops, **Then** the output
   is identical.
2. **Given** the generated data, **When** any record or document is inspected, **Then** it is
   marked as synthetic.

### User Story 5 - Caseworker sees why a case was decided (Priority: P2)

A caseworker opens a determined case and sees the result and, rule by rule, what was checked.

**Why this priority**: A determination a caseworker can't inspect can't be approved with
confidence.

**Independent Test**: In the browser, open seeded determined cases as a caseworker (Eligible,
Ineligible and Cannot determine) and compare each rule shown with the stored determination.

**Acceptance Scenarios**:

1. **Given** a determined case, **When** the caseworker opens it, **Then** they see the result,
   the reason code, the as-of date and rule set version, and for each rule its ID, inputs used,
   threshold and outcome.
2. **Given** a "Cannot determine" result, **When** the caseworker opens the case, **Then** the
   missing items are listed.

### Edge Cases

- Income exactly at the limit: eligible (limit is inclusive).
- Applicant turns 19 or 65 within the coverage period: age is evaluated on the as-of date.
- Household size changes between years: each year uses that year's household size.
- An as-of date with no rule set in force: "Cannot determine" with reason "no rules for date".
- Zero income: eligible on the income rule.
- One rule fails and another lacks information: Ineligible, listing the missing item too.
- Weekly pay of $400: monthly income $1,733.33 (400 × 52 ÷ 12).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-003-01**: The system MUST evaluate these rules for adults 19–64 qualifying on income:
  (1) lives in Illinois; (2) aged 19–64 on the as-of date; (3) citizenship or qualifying
  immigration status attested; (4) identity verified; (5) not entitled to Medicare;
  (6) household income at or below 138% of the federal poverty level for the household size.
- **FR-003-02**: Results MUST be one of Eligible, Ineligible or Cannot determine.
- **FR-003-03**: Missing information MUST produce "Cannot determine" with the missing items
  listed, never "Ineligible".
- **FR-003-04**: Identical inputs and as-of date MUST always produce identical results and
  explanations.
- **FR-003-05**: Each result MUST include, per rule: rule ID, inputs used, threshold, outcome and
  policy reference.
- **FR-003-06**: Rule sets and income limits MUST be versioned by effective date; at least the
  previous and current program years MUST be loaded.
- **FR-003-07**: Evaluation MUST use the rule set in force on the as-of date.
- **FR-003-08**: Evaluation MUST have no side effects and depend on nothing but its inputs.
- **FR-003-09**: A set of at least 30 known-answer cases MUST cover every rule, every edge case
  above and both program years.
- **FR-003-10**: The synthetic data generator MUST be reproducible from a fixed seed and produce
  200 households across 2 coverage years (previous and current program years), household sizes
  1–6, with 60% (±5 points) under the income limit.
- **FR-003-11**: The data set MUST include 15% (±3 points) income mismatches between declared and
  documented income, plus multiple jobs, zero income, household changes between years and
  missing documents.
- **FR-003-12**: The data set MUST include pay stub documents (weekly, bi-weekly and monthly),
  10% (±3 points) of them deliberately poor quality, each with a visible "SYNTHETIC" marker.
- **FR-003-13**: The data set MUST include the test sets for other features: 10–20 pay stubs with
  expected extracted values (002), the known-answer cases (003), households due for
  redetermination during the demo window (007), and expected metric values (008).
- **FR-003-14**: Demo users from 000 MUST be linked to specific households chosen to show the demo
  scenarios.
- **FR-003-15**: Poverty guideline values MUST be held in versioned configuration. Project values
  (annual, per household): previous program year $15,000 for one person plus $5,000 for each
  additional person; current program year $15,500 for one person plus $5,200 for each additional
  person. The monthly income limit is 138% of the annual value divided by 12, rounded down to the
  whole dollar (for example, one person in the current year: $1,782).
- **FR-003-16**: Residency, citizenship or immigration status and Medicare entitlement MUST be
  attested facts on each household member: seeded for seeded households, and taken from the
  application form (FR-001-24) or redetermination response for new ones. Identity and income are
  checked through the simulated verification sources (005, FR-002-13).
- **FR-003-17**: Household monthly income MUST be the sum, over household members, of each
  member's documented monthly income from verified pay stubs (002), across all of their jobs. A
  member declaring zero income counts as zero on their attestation. A declared job without a
  usable pay stub (FR-002-15) makes income missing information.
- **FR-003-18**: Monthly income from a pay stub MUST be gross pay × 52 ÷ 12 for weekly, × 26 ÷ 12
  for bi-weekly, × 2 for semi-monthly and × 1 for monthly pay, rounded to the nearest cent. For a
  job with several stubs, the most recent stub is used.
- **FR-003-19**: Evaluation MUST take a household snapshot (members, attested facts, verified
  income) captured for the case, not the household's current record, so later changes do not
  alter earlier determinations. Household size is the number of members in the snapshot.
- **FR-003-20**: If any rule fails, the result MUST be Ineligible (also listing any missing
  items). The result is Cannot determine only when no rule fails and at least one rule lacks
  information.
- **FR-003-21**: Program years MUST be calendar years: the previous program year is 2025 and the
  current one is 2026. The as-of date is the case's received date for a new application, and the
  redetermination's start date for a redetermination, both on the case clock (FR-001-13).
- **FR-003-22**: The data set MUST include completed history loaded directly into the stores
  (not run through workflows): decided cases from the previous program year and current coverage
  periods, with their determinations, pre-written explanations, notices, review tasks and
  caseworker actions, so that applicant history (004), redeterminations (007) and metric expected
  values (008) work from a fresh reset. Pre-written explanations meet the same checks as
  generated ones (FR-004-11).
- **FR-003-23**: The case page (FR-001-27) MUST show each determination: result, reason code,
  as-of date, rule set version and, for each rule, its ID, inputs used, threshold and outcome
  (FR-003-05), with the missing items for "Cannot determine". (Was FR-006-09, determinations
  part.)

### Key Entities

- **Household**: members, sizes, address state, declared income, linked documents.
- **Household snapshot**: the members, attested facts and verified monthly income captured for
  one case; the input to evaluation (FR-003-19).
- **Rule set**: the rules and income limits in force for a program year, with effective dates.
- **Determination**: result, as-of date, rule set version and the per-rule explanation.
- **Synthetic data set**: generated households, cases, documents and test sets, with the seed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-003-01**: 100% of known-answer cases pass on every run.
- **SC-003-02**: 100% of determinations include a complete explanation for every rule.
- **SC-003-03**: Generating the data set twice with the same seed produces identical records and
  identical document content (text and values).
- **SC-003-04**: Every other lane can load the data set and its test sets without changes.

## Assumptions

- Income limits are project values for this training build (FR-003-15), modelled on the federal
  poverty guidelines but deliberately simplified.
- Household composition and income counting are simplified to monthly gross income for the
  3-day build; this simplification is stated in the demo.
- Residency, citizenship, immigration and Medicare facts are attested (FR-003-16); identity and
  income checks come from the simulated verification sources (005).
- Evaluation is a pure function: `evaluate(household snapshot, as-of date)`.
