# Feature Specification: Eligibility Rules and Synthetic Data

**Feature Branch**: `feature/003-eligibility-rules`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Deterministic Medicaid eligibility rules engine and synthetic data set"

## Lane & Dependencies

- **Lane**: A (workflows and decisions)
- **Provides**: determinations with explanation traces for any household and as-of date; the
  synthetic data set and test sets every lane uses. Used by 001, 002, 006, 007 and 008.
- **Depends on**: 000 (configuration). Nothing else; it must work standalone.
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

### Edge Cases

- Income exactly at the limit: eligible (limit is inclusive).
- Applicant turns 19 or 65 within the coverage period: age is evaluated on the as-of date.
- Household size changes between years: each year uses that year's household size.
- An as-of date with no rule set in force: "Cannot determine" with reason "no rules for date".
- Zero income: eligible on the income rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-003-01**: The system MUST evaluate these rules for adults 19–64 qualifying on income:
  (1) lives in Illinois; (2) aged 19–64 on the as-of date; (3) citizenship or qualifying
  immigration status verified; (4) identity verified; (5) not entitled to Medicare;
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
  about 200 households across 3 coverage years, household sizes 1–6, with about 60% under the
  income limit.
- **FR-003-11**: The data set MUST include about 15% income mismatches between declared and
  documented income, plus multiple jobs, zero income, household changes between years and
  missing documents.
- **FR-003-12**: The data set MUST include pay stub documents (weekly, bi-weekly and monthly),
  about 10% of them deliberately poor quality, each with a visible "SYNTHETIC" marker.
- **FR-003-13**: The data set MUST include the test sets for other features: 10–20 pay stubs with
  expected extracted values (002), the known-answer cases (003), households due for
  redetermination during the demo window (007), and expected metric values (008).
- **FR-003-14**: Demo users from 000 MUST be linked to specific households chosen to show the demo
  scenarios.

### Key Entities

- **Household**: members, sizes, address state, declared income, linked documents.
- **Rule set**: the rules and income limits in force for a program year, with effective dates.
- **Determination**: result, as-of date, rule set version and the per-rule explanation.
- **Synthetic data set**: generated households, cases, documents and test sets, with the seed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-003-01**: 100% of known-answer cases pass on every run.
- **SC-003-02**: 100% of determinations include a complete explanation for every rule.
- **SC-003-03**: Generating the data set twice with the same seed produces byte-identical output.
- **SC-003-04**: Every other lane can load the data set and its test sets without changes.

## Assumptions

- Income limits use the published federal poverty guidelines for each program year; the team
  copies the values into configuration and records the source. 138% reflects the adult income
  limit as we understand it and must be confirmed against the current Illinois figures.
- Household composition and income counting are simplified to monthly gross income for the
  3-day build; this simplification is stated in the demo.
- Citizenship, immigration and identity checks come from the simulated verification sources (005).
