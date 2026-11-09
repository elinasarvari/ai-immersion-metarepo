# Feature Specification: Program Metrics

**Feature Branch**: `feature/008-program-metrics`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Program metrics reporting from case history"

## Lane & Dependencies

- **Lane**: C (platform and experience)
- **Provides**: a reporting store built from case history and a program metrics page.
- **Depends on**: 001 (case history, review tasks), 003 (data set and expected metric values),
  006 (console shell), 007 (redetermination outcomes).
- **Out of scope**: federal reporting file formats, real-time dashboards, exports, metrics for
  individual caseworkers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See program health (Priority: P1)

A supervisor opens the program metrics page and sees how the program is performing this month
and over time.

**Why this priority**: These are the numbers agencies manage and report by, and they show the AI
is helping.

**Independent Test**: Load the seed data, refresh the reporting store and confirm every metric
matches its expected value.

**Acceptance Scenarios**:

1. **Given** refreshed data, **When** the supervisor opens the page, **Then** they see average time
   to decision, share decided within the deadline, automatic renewal rate, procedural denial
   rate, AI override rate and open reviews by age.
2. **Given** the page, **When** the supervisor picks a month, **Then** every metric updates for
   that month.

---

### User Story 2 - Trustworthy numbers (Priority: P1)

The team can show every metric is correct and that rebuilding the reporting store gives the
same answers.

**Why this priority**: Wrong metrics are worse than none.

**Independent Test**: Refresh twice and compare; compare each metric with its hand-calculated
expected value.

**Acceptance Scenarios**:

1. **Given** the same source data, **When** the reporting store is refreshed twice, **Then** the
   results are identical.
2. **Given** the seed data, **When** metrics are computed, **Then** each matches its expected value.

---

### User Story 3 - No personal data in reporting (Priority: P1)

The reporting store holds no names, contact details or document contents.

**Why this priority**: Reporting should not add privacy risk.

**Independent Test**: Scan the reporting store's fields and sample values for personal data.

**Acceptance Scenarios**:

1. **Given** the refreshed reporting store, **When** it is scanned, **Then** no personal fields are
   found and households appear only under pseudonymous keys.

---

### User Story 4 - Refresh on schedule or on demand (Priority: P2)

The reporting store refreshes on a schedule, and a team member can refresh it on demand for the
demo.

**Why this priority**: Fresh numbers during the demo.

**Independent Test**: Trigger an on-demand refresh after creating a new case and confirm the
metrics change.

**Acceptance Scenarios**:

1. **Given** a new decided case, **When** an on-demand refresh completes, **Then** the metrics
   include it.

### Edge Cases

- A month with no decisions: metrics show "no data", not zero.
- A refresh fails midway: the previous complete results stay visible.
- A metric's denominator is zero: shown as "not applicable".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-008-01**: The system MUST refresh the reporting store from case data on a schedule and on
  demand; two refreshes of the same source data MUST give identical results.
- **FR-008-02**: The reporting store MUST hold pseudonymous household keys only, with no names,
  contact details or document content.
- **FR-008-03**: The program metrics page MUST show average time to decision, share decided
  within the deadline, automatic renewal rate, procedural denial rate, AI override rate and
  open reviews by age, each filterable by month.
- **FR-008-04**: Each metric MUST match an expected value worked out by hand on the seed data.
- **FR-008-05**: A failed refresh MUST leave the previous complete results in place.
- **FR-008-06**: Metrics with no data or a zero denominator MUST say so instead of showing zero.
- **FR-008-07**: Only supervisors and caseworkers MAY view the program metrics page.

### Key Entities

- **Metric**: name, definition, period, value.
- **Reporting store**: facts (case events, determinations, review tasks) and descriptive
  dimensions (household key, program, date, coverage period).

Metric definitions:

- **Average time to decision**: days from application received to decision, for cases decided
  in the period.
- **Decided within deadline**: decisions on new applications made within 45 days ÷ all
  decisions on new applications in the period (redeterminations have no 45-day deadline).
- **Automatic renewal rate**: redeterminations renewed with no applicant action ÷
  redeterminations started.
- **Procedural denial rate**: denials with reason code "missing information" (FR-001-16) ÷ all
  denials.
- **AI override rate**: caseworker overrides ÷ AI findings reviewed.
- **Open reviews by age**: open review tasks by days open (0–1, 2–3, 4 or more).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-008-01**: 100% of metrics match their expected values on the seed data.
- **SC-008-02**: Two consecutive refreshes produce identical results.
- **SC-008-03**: Zero personal fields found in the reporting store.
- **SC-008-04**: An on-demand refresh completes in under 1 minute on the seed data.

## Assumptions

- Metrics cover the single program in scope (Illinois Medicaid, adults 19–64).
- If time runs short, the fallback is four metrics: average time to decision, decided within
  deadline, automatic renewal rate and AI override rate.
