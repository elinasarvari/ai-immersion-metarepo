# Feature Specification: Redeterminations

**Feature Branch**: `feature/007-redeterminations`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Annual Medicaid redeterminations with automatic renewal first"

## Lane & Dependencies

- **Lane**: A (workflows and decisions)
- **Provides**: the yearly redetermination process for every enrolled household. Used by 006
  (applicant view) and 008 (metrics).
- **Depends on**: 001 (case lifecycle, review tasks, notices, demo clock), 002 (verification and
  renewal form drafting), 003 (rules, data set), 005 (verification sources). 002 and 005 are
  stubbed until ready.
- **Out of scope**: mid-period change reporting, appeals, the reconsideration period after
  coverage ends, outreach by mail, phone or text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic renewal when nothing is missing (Priority: P1)

Before a household's coverage period ends, the system checks the information it already holds.
If the household is still eligible and nothing is missing, coverage is renewed with nothing
asked of the applicant.

**Why this priority**: This is the change that prevents procedural coverage loss.

**Independent Test**: Advance the clock to the start window for a household that is still
eligible and confirm renewal without any applicant action.

**Acceptance Scenarios**:

1. **Given** a coverage period 60 days from ending, **When** that day arrives, **Then** a
   redetermination starts for the household.
2. **Given** the household is still eligible on held data with nothing missing, **When** the check
   completes, **Then** coverage is renewed for 12 months and a favourable notice from the fixed
   template is delivered to the portal, with nothing asked of the applicant.

---

### User Story 2 - Ask only for what's missing (Priority: P1)

If information is missing or out of date, the applicant gets a pre-filled form listing only the
items to confirm or provide.

**Why this priority**: Short, specific requests get answered.

**Independent Test**: Use a household with a changed job and confirm the form lists only income.

**Acceptance Scenarios**:

1. **Given** held data that is missing or out of date, **When** the check completes, **Then** a
   pre-filled form listing only those items is drafted (002) and goes to a caseworker for
   approval; once approved, the applicant has 30 days to respond.
2. **Given** the applicant responds, **When** the response arrives, **Then** it goes through the
   normal verification and determination steps.

---

### User Story 3 - No automatic loss of coverage (Priority: P1)

If the applicant does not respond within 30 days, a caseworker reviews the case. Coverage never
ends automatically.

**Why this priority**: Directly addresses the procedural disenrollment problem.

**Independent Test**: Advance the clock past the response deadline with no response and confirm
a review task, with coverage unchanged.

**Acceptance Scenarios**:

1. **Given** no response within 30 days, **When** the deadline passes, **Then** a caseworker review
   task is created and coverage continues.
2. **Given** the coverage period end arrives while the review is still open, **When** it passes,
   **Then** coverage continues and the task is flagged as escalated.

---

### User Story 4 - See upcoming redeterminations (Priority: P3)

Caseworkers can see households whose redeterminations start in the next 30 days.

**Why this priority**: Helps planning; feeds metrics.

**Independent Test**: List upcoming redeterminations for the seeded data and compare with
expected.

**Acceptance Scenarios**:

1. **Given** seeded households, **When** the caseworker views upcoming redeterminations, **Then**
   households starting in the next 30 days are listed with their coverage end dates.

### Edge Cases

- The household is now ineligible on held data: the applicant is asked to confirm their details
  first; any adverse outcome waits for caseworker approval.
- The household has an open case already: the redetermination waits until it is decided.
- A redetermination is started twice for the same period: only one runs.
- The system is down on the start day: the redetermination starts when it is back up.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-007-01**: When a coverage period is 60 days from ending, the system MUST start a
  redetermination for that household.
- **FR-007-02**: The system MUST first try to renew from data it already holds; if the household
  is still eligible with nothing missing, it MUST renew without asking the applicant for
  anything and deliver a favourable template notice.
- **FR-007-03**: If information is missing, the system MUST have a pre-filled form drafted listing
  only the items to confirm, send it for caseworker approval, and once approved give the
  applicant 30 days to respond.
- **FR-007-04**: If the applicant has not responded within 30 days, the system MUST create a
  caseworker review task, and coverage MUST NOT end automatically at any point; it ends only by
  an approved caseworker decision.
- **FR-007-05**: A renewal MUST create a new 12-month coverage period linked to the household's
  history.
- **FR-007-06**: Any adverse redetermination outcome MUST wait for caseworker approval.
- **FR-007-07**: Only one redetermination MAY run per household per coverage period.
- **FR-007-08**: Redeterminations MUST use the same verification, rules, explanation and review
  steps as new applications, but have no 45-day decision deadline.
- **FR-007-09**: Caseworkers MUST be able to list redeterminations starting in the next 30 days.
- **FR-007-10**: A caseworker or supervisor MUST be able to start a household's redetermination on
  demand (for demos and catch-up), subject to FR-007-07.
- **FR-007-11**: The 60-day start and 30-day response window MUST follow the demo time scale and
  demo clock (FR-001-13, FR-001-15) when the demo profile is on.
- **FR-007-12**: A redetermination MUST end with one outcome: renewed automatically, renewed after
  response, or ended by caseworker decision.

### Key Entities

- **Coverage period**: start and end dates of a household's coverage for a program year.
- **Redetermination**: a case of type "redetermination" linked to the period it renews, using the
  001 states, with one outcome from FR-007-12.
- **Renewal form**: pre-filled items to confirm, deadline, approval status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-007-01**: 100% of seeded households still eligible with complete data renew with no
  applicant action.
- **SC-007-02**: 100% of renewal forms list only the missing or out-of-date items.
- **SC-007-03**: Zero coverage periods end automatically in testing.
- **SC-007-04**: The demo shows both an automatic renewal and a renewal needing one document in
  under 2 minutes using the demo clock.
- **SC-007-05**: A workflow replay test against recorded redetermination histories passes on every
  PR.

## Assumptions

- Illinois calls Medicaid renewals "redeterminations"; federal rules expect states to renew from
  available data before asking the applicant.
- The 60-day start, 30-day response window and 12-month coverage period are project values for
  this training build. All day counts are calendar days.
