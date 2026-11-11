# Feature Specification: Redeterminations

**Feature Branch**: `feature/007-redeterminations`

**Created**: 2026-11-09

**Status**: Draft (MVP scope, 2026-11-11: all AI removed)

**Input**: User description: "Annual Medicaid redeterminations with automatic renewal first"

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: the redetermination process for an enrolled household, and its screens for
  caseworkers and applicants. Used by 008 (metrics).
- **Depends on**: 001 (case lifecycle, the case page), 003 (rules, data set) and 010 (review
  tasks), all on `main`; 011 (notices, the wait with a deadline, the demo clock); 002 (the
  income check, the reference lookup FR-002-22 and pay stub upload).
- **Two parts, built in this order**:
  - **007a Automatic renewal** (US1, US3, US6): start on demand, renew from held data, review
    when there is no response. Starts immediately against the notice types and timer names
    agreed with 011, and is joined to 011 when it lands.
  - **007b Applicant response** (US2, US5): the renewal form and the applicant's answer. Starts
    after 011, because it reuses 011's wait, notices and response screens.
- **Out of scope**: mid-period change reporting, appeals, the reconsideration period after
  coverage ends, outreach by mail, phone or text.

Story and requirement IDs are not reused. Deferred ones are listed at the end of the
requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 6 - Start a redetermination on demand (Priority: P1, 007a)

A caseworker or supervisor opens a household page and starts its redetermination.

**Why this priority**: In the MVP this is the only way a redetermination starts.

**Independent Test**: In the browser, open a household with active coverage as a supervisor, press
"Start redetermination", follow the link to the new case, then press it again and confirm no
second redetermination starts.

**Acceptance Scenarios**:

1. **Given** a household with active coverage, **When** a caseworker or supervisor presses "Start
   redetermination" on its household page, **Then** a redetermination opens and the page links to
   it.
2. **Given** a redetermination already running for that coverage period, **When** the button is
   pressed again, **Then** no second one starts and the page links to the running one.

---

### User Story 1 - Automatic renewal when nothing is missing (Priority: P1, 007a)

When a redetermination starts, the system checks the information it already holds. If the
household is still eligible and nothing is missing or out of date, coverage is renewed with
nothing asked of the applicant.

**Why this priority**: This is the change that prevents procedural coverage loss.

**Independent Test**: Start a redetermination for a seeded household that is still eligible and
confirm renewal without any applicant action.

**Acceptance Scenarios**:

1. **Given** the household is still eligible on held data with nothing missing or out of date,
   **When** the check completes, **Then** coverage is renewed for 12 months and a favourable
   notice from the fixed template is delivered to the portal, with nothing asked of the
   applicant.

---

### User Story 3 - No automatic loss of coverage (Priority: P1, 007a)

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

### User Story 2 - Ask only for what's missing (Priority: P1, 007b)

If information is missing or out of date, the applicant gets a pre-filled form listing only the
items to confirm or provide.

**Why this priority**: Short, specific requests get answered.

**Independent Test**: Use a seeded household with a changed job and confirm the form lists only
that job's income.

**Acceptance Scenarios**:

1. **Given** held data that is missing or out of date, **When** the check completes, **Then** a
   pre-filled form listing only those items is produced from the fixed template and goes to a
   caseworker for approval; once approved, the applicant has 30 days to respond.
2. **Given** the applicant responds, **When** the response arrives, **Then** it goes through the
   normal income check and determination steps.

---

### User Story 5 - Applicant responds to a renewal (Priority: P1, 007b)

An applicant whose redetermination needs something from them sees what to confirm and by when,
confirms or corrects the pre-filled details, and uploads pay stubs.

**Why this priority**: Without a way to respond, every renewal that needs one document ends in
review; this is one of the demo journeys.

**Independent Test**: In the browser, sign in as the demo applicant whose renewal needs one
document, confirm the details, upload a pay stub with its details, and confirm the
redetermination continues and renews.

**Acceptance Scenarios**:

1. **Given** an applicant with a redetermination waiting for them, **When** they sign in, **Then**
   they see what they need to confirm, if anything, and the deadline.
2. **Given** the renewal form, **When** the applicant confirms or corrects the pre-filled household
   members, jobs and income and uploads pay stubs, **Then** a new household snapshot is created
   and the redetermination continues.

### Edge Cases

- The household is now ineligible on held data: the applicant is asked to confirm their details
  first; any adverse outcome waits for caseworker approval.
- The household has an open case already: the redetermination waits until it is decided.
- A redetermination is started twice for the same period: only one runs.
- The reference lookup reports a job the household did not declare: the form asks about that
  job only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-007-02**: The system MUST first try to renew from data it already holds; if the household
  is still eligible with nothing missing or out of date, it MUST renew without asking the
  applicant for anything and deliver a favourable template notice.
- **FR-007-03**: If information is missing or out of date, the system MUST produce a pre-filled
  form from the fixed template (FR-011-06) listing only the items to confirm, send it for
  caseworker approval, and once approved give the applicant 30 days to respond. (Revised: no
  AI draft.)
- **FR-007-04**: If the applicant has not responded within 30 days, the system MUST create a
  caseworker review task, and coverage MUST NOT end automatically at any point; it ends only by
  an approved caseworker decision.
- **FR-007-05**: A renewal MUST create a new 12-month coverage period linked to the household's
  history.
- **FR-007-06**: Any adverse redetermination outcome MUST wait for caseworker approval.
- **FR-007-07**: Only one redetermination MAY run per household per coverage period. A
  redetermination's case identifier is derived from the coverage period it renews, so a second
  start for the same period finds the running one and links to it instead (mechanism in
  [mvp-contracts.md](../mvp-contracts.md) section 2; it replaces the deferred FR-007-15).
- **FR-007-08**: Redeterminations MUST use the same income check, rules, explanation and review
  steps as new applications, but have no 45-day decision deadline.
- **FR-007-10**: A caseworker or supervisor MUST be able to start a household's redetermination on
  demand, subject to FR-007-07.
- **FR-007-11**: The 30-day response window MUST follow the demo time scale and demo clock
  (FR-001-13, FR-011-04, FR-011-05) when the demo profile is on.
- **FR-007-12**: A redetermination MUST end with one outcome: renewed automatically, renewed after
  response, or ended by caseworker decision. An ending carries a reason code: income over limit,
  other rule not met, or missing information (no response).
- **FR-007-13**: The renewal check MUST look up identity and income in the reference lookup
  (FR-002-22) and evaluate the held household snapshot with that income as of the
  redetermination's start date (FR-003-21). Information is "missing or out of date" when the
  lookup reports income differing from held income by more than 10%, the lookup reports a job
  the household has not declared, a declared job has no income in the lookup, or identity no
  longer matches. Renewal is automatic only when the result is Eligible and nothing is missing
  or out of date. (Revised: an ordinary lookup, not simulated sources.)
- **FR-007-14**: A renewed coverage period MUST start the day after the previous one ends. While a
  redetermination review is open after the coverage end date, the coverage period's status MUST
  be "continued pending review" and coverage continues. The `coverage_end` timer from 010
  (FR-010-02) sets this status and escalates the open review task. This feature uses that timer
  and does not add its own.
- **FR-007-16**: An applicant's redetermination response MUST let them confirm or correct the
  pre-filled items (household members, jobs and income) and upload pay stubs; it creates a new
  household snapshot for the case (FR-003-19).
- **FR-007-18**: Caseworkers and supervisors MUST be able to open a household page (members,
  coverage periods and cases) and start the household's redetermination from it (FR-007-10).
  When one is already running for the period, the page links to it instead. (Was FR-006-17.)
- **FR-007-19**: When an applicant signs in with a redetermination waiting for them, the portal
  MUST show what they need to confirm, if anything, and the deadline, and let them respond as in
  FR-007-16, uploading pay stubs with FR-002-17. (Was FR-006-08, redetermination part.)

### Deferred

| ID | What it was |
|---|---|
| FR-007-01, FR-007-15, SC-007-05 | Starting automatically 60 days before coverage ends, on a daily schedule; the schedule and the button giving one run; the replay test on every PR |
| US4, FR-007-09, FR-007-17 | The upcoming redeterminations page |

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

## Assumptions

- Illinois calls Medicaid renewals "redeterminations"; federal rules expect states to renew from
  available data before asking the applicant.
- The 30-day response window and 12-month coverage period are project values for this training
  build. All day counts are calendar days.
- The synthetic data set (003) includes households due for redetermination with reference
  income that agrees and disagrees with held income. **These are not on `main` yet:** seed tasks
  S-01, S-02 and S-04 in [mvp-seed-data-tasks.md](../mvp-seed-data-tasks.md) add the reference
  records, the expected renewal paths, and the two demo households: household E renews
  automatically (US1), and `applicant4` / household D needs one pay stub (US2, US5).
- The 30-day wait is the `redetermination_response_deadline` timer, built with 011's wait
  helper. The applicant's answer arrives on 011's `applicant_response` signal
  ([mvp-contracts.md](../mvp-contracts.md) section 2).
- This feature never edits `apps/worker/workflows/case.py`. Its path lives in
  `apps/worker/workflows/redetermination.py` and is called from the hook added by the contracts
  PR. Until 011 lands, 007a tests against the stubs that hook provides.
