# Feature Specification: Redeterminations

**Feature Branch**: `feature/007-redeterminations`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Annual Medicaid redeterminations with automatic renewal first"

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: the yearly redetermination process for every enrolled household, and its screens
  for caseworkers and applicants. Used by 008 (metrics).
- **Depends on**: 001 (case lifecycle, the case page), 010 (review tasks), 011 (notices, demo clock), 002 (verification and
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

**Independent Test**: In the browser, open the upcoming redeterminations page as a caseworker for
the seeded data and compare the list with the expected households.

**Acceptance Scenarios**:

1. **Given** seeded households, **When** the caseworker opens the upcoming redeterminations page,
   **Then** households starting in the next 30 days are listed with their coverage end dates, each
   linking to its household page.

### User Story 5 - Applicant responds to a renewal (Priority: P1)

An applicant whose redetermination needs something from them sees what to confirm and by when,
confirms or corrects the pre-filled details, and uploads pay stubs.

**Why this priority**: Without a way to respond, every renewal that needs one document ends in
review; this is one of the demo journeys.

**Independent Test**: In the browser, sign in as the demo applicant whose renewal needs one
document, confirm the details, upload a pay stub, and confirm the redetermination continues and
renews.

**Acceptance Scenarios**:

1. **Given** an applicant with a redetermination waiting for them, **When** they sign in, **Then**
   they see what they need to confirm, if anything, and the deadline.
2. **Given** the renewal form, **When** the applicant confirms or corrects the pre-filled household
   members, jobs and income and uploads pay stubs, **Then** a new household snapshot is created
   and the redetermination continues.

---

### User Story 6 - Start a redetermination on demand (Priority: P2)

A caseworker or supervisor opens a household page and starts its redetermination, for demos and
catch-up.

**Why this priority**: The demo can't wait for the daily schedule.

**Independent Test**: In the browser, open a household with active coverage as a supervisor, press
"Start redetermination", follow the link to the new case, then press it again and confirm no
second redetermination starts.

**Acceptance Scenarios**:

1. **Given** a household with active coverage, **When** a caseworker or supervisor presses "Start
   redetermination" on its household page, **Then** a redetermination opens and the page links to
   it.
2. **Given** a redetermination already running for that coverage period, **When** the button is
   pressed again, **Then** no second one starts and the page links to the running one.

### Edge Cases

- The household is now ineligible on held data: the applicant is asked to confirm their details
  first; any adverse outcome waits for caseworker approval.
- The household has an open case already: the redetermination waits until it is decided.
- A redetermination is started twice for the same period: only one runs.
- The system is down on the start day: the redetermination starts when it is back up.
- The income source reports a new job the household did not declare: the form asks about that
  job only.

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
  demo clock (FR-001-13, FR-011-04, FR-011-05) when the demo profile is on.
- **FR-007-12**: A redetermination MUST end with one outcome: renewed automatically, renewed after
  response, or ended by caseworker decision. An ending carries a reason code: income over limit,
  other rule not met, or missing information (no response).
- **FR-007-13**: The renewal check MUST re-verify identity and income with the simulated sources
  (005) and evaluate the held household snapshot with that income as of the redetermination's
  start date (FR-003-21). Information is "missing or out of date" when a source reports income
  differing from held income by more than 10%, a source reports a job the household has not
  declared, a declared job has no verified income, or identity no longer matches. Renewal is
  automatic only when the result is Eligible and nothing is missing or out of date.
- **FR-007-14**: A renewed coverage period MUST start the day after the previous one ends. While a
  redetermination review is open after the coverage end date, the coverage period's status MUST
  be "continued pending review" and coverage continues.
- **FR-007-15**: A redetermination started on demand (FR-007-10) MUST run exactly the same process
  as one started by the daily schedule; if both happen for the same period, only one runs
  (FR-007-07).
- **FR-007-16**: An applicant's redetermination response MUST let them confirm or correct the
  pre-filled items (household members, jobs and income) and upload pay stubs; it creates a new
  household snapshot for the case (FR-003-19).
- **FR-007-17**: The caseworker console MUST have an upcoming redeterminations page listing the
  households whose redeterminations start in the next 30 days, with their coverage end dates
  (FR-007-09). (Was FR-006-16.)
- **FR-007-18**: Caseworkers and supervisors MUST be able to open a household page (members,
  coverage periods and cases) and start the household's redetermination from it (FR-007-10).
  When one is already running for the period, the page links to it instead. (Was FR-006-17.)
- **FR-007-19**: When an applicant signs in with a redetermination waiting for them, the portal
  MUST show what they need to confirm, if anything, and the deadline, and let them respond as in
  FR-007-16, uploading pay stubs with FR-002-17. (Was FR-006-08, redetermination part.)

### Key Entities

- **Coverage period**: start and end dates of a household's coverage, and its status (active,
  continued pending review, renewed, ended).
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
