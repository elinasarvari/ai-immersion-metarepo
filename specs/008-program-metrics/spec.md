# Feature Specification: Program Metrics

**Feature Branch**: `feature/008-program-metrics`

**Created**: 2026-11-09

**Status**: Draft (MVP scope, 2026-11-11)

**Input**: User description: "Program metrics reporting from case history"

## Lane & Dependencies

- **Lane**: Platform & UI (one read-only endpoint and the metrics page)
- **Provides**: a program metrics page.
- **Depends on**: 001 (case history), 010 (review outcomes), 003 (data set, including seeded
  past decisions and redetermination outcomes, and the expected metric values), 000 (app
  shell). 000, 001 and 010 are on `main`. **The data set on `main` has past decisions but no
  redetermination outcomes, no expected automatic renewal rate, and a procedural denial rate
  with a different denominator.** Seed task S-05 in
  [mvp-seed-data-tasks.md](../mvp-seed-data-tasks.md) adds and fixes them. Until it lands,
  build against a small fixture worked out by hand. It reads 007's redetermination outcomes
  once they exist.
- **Out of scope**: federal reporting file formats, real-time dashboards, exports, metrics for
  individual caseworkers, any metric about AI.

Story and requirement IDs are not reused. Removed and deferred ones are listed at the end of
the requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See program health (Priority: P1)

A supervisor opens the program metrics page and sees how the program is performing this month
and over time.

**Why this priority**: These are the numbers agencies manage and report by.

**Independent Test**: Load the seed data, open the page and confirm every metric matches its
expected value.

**Acceptance Scenarios**:

1. **Given** the seed data, **When** the supervisor opens the page, **Then** they see average time
   to decision, share decided within the deadline, automatic renewal rate and procedural denial
   rate.
2. **Given** the page, **When** the supervisor picks a month, **Then** every metric updates for
   that month.
3. **Given** a newly decided case, **When** the page is reloaded, **Then** the metrics include it.

---

### User Story 2 - Trustworthy numbers (Priority: P1)

The team can show every metric is correct.

**Why this priority**: Wrong metrics are worse than none.

**Independent Test**: Compare each metric with its hand-calculated expected value; request the
metrics twice and compare.

**Acceptance Scenarios**:

1. **Given** the seed data, **When** metrics are computed, **Then** each matches its expected value.
2. **Given** unchanged data, **When** the metrics are requested twice, **Then** the results are
   identical.

### Edge Cases

- A month with no decisions: metrics show "no data", not zero.
- A metric's denominator is zero: shown as "not applicable".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-008-03**: The program metrics page MUST show average time to decision, share decided
  within the deadline, automatic renewal rate and procedural denial rate, each filterable by
  month. (Revised: four metrics.)
- **FR-008-04**: Each metric MUST match an expected value worked out by hand on the seed data.
- **FR-008-06**: Metrics with no data or a zero denominator MUST say so instead of showing zero.
- **FR-008-07**: Only supervisors and caseworkers MAY view the program metrics page.
- **FR-008-08**: Metrics MUST use case-clock dates (FR-001-13). A metric for a month counts
  cases decided in that month (for the automatic renewal rate: redeterminations that ended in
  that month).
- **FR-008-09**: Metrics MUST be computed from the case data each time the page asks for them.
  No copy of the data is kept, and the response MUST contain only the metric values: no names,
  household identifiers or case identifiers.

### Deferred

| ID | What it was |
|---|---|
| FR-008-01, FR-008-05, US4 | A separate reporting store refreshed on a schedule and on demand, and keeping the last good results when a refresh fails |
| FR-008-02, US3 | Pseudonymous household keys in the reporting store (no store, so nothing to pseudonymise; FR-008-09 covers the page) |
| Open reviews by age | The sixth metric |

### Removed

| ID | What it was |
|---|---|
| AI override rate | A metric about AI output; there is none in the MVP |

### Key Entities

- **Metric**: name, definition, period, value.

Metric definitions:

- **Average time to decision**: days from application received to decision, for new
  applications decided in the period (redeterminations are counted by the renewal rate
  instead).
- **Decided within deadline**: decisions on new applications made within 45 days ÷ all
  decisions on new applications in the period (redeterminations have no 45-day deadline).
- **Automatic renewal rate**: redeterminations renewed automatically ÷ redeterminations that
  ended in the period.
- **Procedural denial rate**: denials and coverage endings with reason code "missing
  information" (FR-001-16, FR-007-12) ÷ all denials and coverage endings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-008-01**: 100% of metrics match their expected values on the seed data.
- **SC-008-02**: Two consecutive requests on unchanged data give identical results.
- **SC-008-03**: Zero personal fields or identifiers in the metrics response.
- **SC-008-04**: The page loads its metrics in under 5 seconds on the seed data. (Was: refresh
  in under 1 minute.)

## Assumptions

- Metrics cover the single program in scope (Illinois Medicaid, adults 19–64).
- The seed data is small enough to compute metrics on request. The reporting store in
  `analytics/` is not used by the MVP.
