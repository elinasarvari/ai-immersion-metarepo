# Feature Specification: Caseworker Console and Applicant Portal

**Feature Branch**: `feature/006-caseworker-applicant-portal`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Caseworker console and applicant portal"

## Lane & Dependencies

- **Lane**: Platform & UI
- **Provides**: the screens caseworkers and applicants use, and the operations behind them.
- **Depends on**: 000 (sign-in, errors), 001 (case states, review tasks, actions), 003
  (determinations), 004 (explanations), 007 (redetermination responses). Builds against stub operations returning
  seed data until those land.
- **Out of scope**: mobile apps, languages other than English, notifications by email or text,
  the program metrics page (008).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Caseworker works the review queue (Priority: P1)

A caseworker sees open review tasks ordered by decision deadline, opens one, sees the finding
with its evidence and citations, and approves, edits or overrides it with a reason.

**Why this priority**: This is how human control actually happens.

**Independent Test**: With seeded review tasks, sign in as a caseworker, act on each task type
and confirm the case resumes.

**Acceptance Scenarios**:

1. **Given** open review tasks, **When** the caseworker opens the queue, **Then** tasks are listed
   by soonest decision deadline, showing reason, days remaining and at-risk status.
2. **Given** an open task, **When** the caseworker opens it, **Then** they see the finding, the
   document values and policy passages cited, and approve, edit and override actions.
3. **Given** an override, **When** the caseworker submits it, **Then** a reason is required, the
   action is recorded, and the case is added to the evaluation set.
4. **Given** a task open for 4 days, **When** a supervisor opens the queue, **Then** the task is
   flagged as escalated, showing how long it has been open.

---

### User Story 2 - Caseworker approves notices (Priority: P1)

A caseworker reviews each drafted request for information, edits it if needed, and approves it
before it reaches the applicant.

**Why this priority**: No notice reaches an applicant without approval.

**Independent Test**: Approve one draft and edit another; confirm only approved versions appear
to the applicant.

**Acceptance Scenarios**:

1. **Given** a drafted notice, **When** the caseworker approves it unchanged, **Then** it is
   delivered to the applicant's portal.
2. **Given** a drafted notice, **When** the caseworker edits and approves it, **Then** the edited
   version is delivered and both versions are kept in the case history.

---

### User Story 3 - Applicant applies and uploads documents (Priority: P1)

An applicant signs in, submits a Medicaid application with declared household and income, and
uploads pay stubs.

**Why this priority**: Starts every new case.

**Independent Test**: Sign in as a demo applicant, submit an application with a pay stub and
confirm a case is opened.

**Acceptance Scenarios**:

1. **Given** a signed-in applicant, **When** they submit a complete application with a pay stub,
   **Then** they see a confirmation with the case reference and decision deadline.
2. **Given** an incomplete application, **When** they try to submit, **Then** each missing field is
   identified and nothing is submitted.

---

### User Story 4 - Applicant sees status, requests and history (Priority: P2)

An applicant sees the status of each open case, any open requests for information with due
dates, and past applications and decisions with explanations.

**Why this priority**: Reduces "what's happening with my case" contacts; shows transparency.

**Independent Test**: Sign in as a returning demo applicant and confirm status, open requests and
history across years.

**Acceptance Scenarios**:

1. **Given** an applicant with an open request for information, **When** they sign in, **Then**
   they see what is needed, the due date, and can upload a response.
2. **Given** an applicant with past decisions, **When** they open their history, **Then** they see
   each coverage period's decision with its plain-language explanation as recorded at the time.
3. **Given** an applicant due for redetermination, **When** they sign in, **Then** they see what
   they need to confirm, if anything, and the deadline.

---

### User Story 5 - Applicants see only their own records (Priority: P1)

An applicant can only ever see their own household's information.

**Why this priority**: Privacy is non-negotiable even with synthetic data.

**Independent Test**: Signed in as applicant A, try to open applicant B's case by changing a
reference; confirm refusal.

**Acceptance Scenarios**:

1. **Given** applicant A is signed in, **When** they request any record belonging to another
   household, **Then** the request is refused, logged, and reveals nothing about whether the
   record exists.

### Edge Cases

- Two caseworkers open the same task: the second action is refused with "already actioned by …".
- An upload is too large or an unsupported type: refused with the allowed sizes and types.
- A session expires mid-form: the applicant's entries are kept and they are asked to sign in.
- Keyboard-only and screen reader users can complete every flow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-006-01**: The review queue MUST list open tasks sorted by decision deadline, showing reason,
  days remaining and at-risk status, with approve, edit and override actions. It is one shared
  queue for all caseworkers, and tasks open 4 days or more are flagged as escalated.
- **FR-006-02**: When a caseworker overrides an AI finding, the system MUST require a reason,
  record it, and store it as an evaluation example read by the evaluation command (FR-002-11).
- **FR-006-03**: When an applicant signs in, the system MUST show the status of each open case and
  any open requests for information with their due dates.
- **FR-006-04**: The system MUST show the applicant's past applications and decisions for every
  coverage period, with the explanation as recorded at the time.
- **FR-006-05**: Applicants MUST see only records belonging to their own household; any other
  request MUST be refused, logged and reveal nothing about whether the record exists.
  Caseworkers and supervisors can see all cases.
- **FR-006-06**: AI-drafted and adverse notices MUST be delivered only after caseworker approval;
  favourable template notices are delivered directly. Edited and original versions MUST both be
  kept.
- **FR-006-07**: Applicants MUST be able to submit an application with household and income
  details and upload pay stubs (PDF or image, up to 10 MB each).
- **FR-006-08**: Applicants MUST be able to respond to a request for information or a
  redetermination by uploading documents and confirming details.
- **FR-006-09**: Caseworkers MUST be able to view a case's full history: states, findings,
  determinations with their explanations, documents, notices and actions.
- **FR-006-10**: All screens MUST meet WCAG 2.1 AA.
- **FR-006-11**: Every screen MUST show a visible "synthetic data" banner.
- **FR-006-12**: A task already actioned MUST refuse further actions and say who acted.
- **FR-006-13**: In the demo profile only, supervisors MUST be able to advance a case's clock
  (FR-001-15) from the case view.

### Key Entities

- **Review queue item**: review task with case reference, reason, days remaining, at-risk flag.
- **Application**: declared household, income and uploaded documents for a new case.
- **Applicant view**: open cases, open requests, history by coverage period.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-006-01**: A caseworker completes a review (open, read evidence, act) in under 2 minutes.
- **SC-006-02**: A demo applicant submits an application with a pay stub in under 5 minutes.
- **SC-006-03**: 100% of cross-household access attempts in testing are refused.
- **SC-006-04**: An automated accessibility check reports zero serious or critical issues on every
  screen.

## Assumptions

- English only; desktop browser first, usable at phone width.
- Applicants use seeded demo accounts linked to synthetic households (000, 003).
