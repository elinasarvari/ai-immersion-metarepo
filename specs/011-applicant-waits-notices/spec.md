# Feature Specification: Applicant Waits, Notices and Demo Clock

**Feature Branch**: `feature/011-applicant-waits-notices`

**Created**: 2026-11-10

**Status**: Draft (MVP scope, 2026-11-11: all AI removed)

**Input**: User description: "Split of 001 case lifecycle: applicant waits, notices and demo clock. Waiting for the applicant with a response deadline, configurable waiting periods with a compressed demo time scale, the notice catalogue, and decision explanations."

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: the "Awaiting applicant" wait and its response deadline; configurable waiting
  periods and the demo time scale; the supervisor "advance clock" action; the catalogue of
  notices sent to applicants, all from fixed templates; storing decision explanations; the
  screens for notices, responses and the demo clock. Used by 007.
- **Depends on**: 001 (cases, states, case history, the case clock, the case page), 010 (review
  reasons and actions) and 000 (configuration profiles, supervisor role), all on `main`, so
  this feature can start immediately. It also uses 002 (missing items for the request for
  information, pay stub upload) and 004 (explanations); until they land it uses a stubbed
  verification result and the rule-by-rule trace (FR-003-05).
- **Agree first**: the notice type names (FR-011-06), the timer names and the applicant-response
  signal, because 007 builds on them. They are drafted in
  [mvp-contracts.md](../mvp-contracts.md) section 2 and merged in the contracts PR before the
  split. This feature owns `apps/worker/workflows/case.py`; 002 and 007 add their steps in
  their own modules, called from hooks the contracts PR adds.
- **Split from**: 001 Case lifecycle (2026-11-10). Old IDs map to new ones: FR-001-05 →
  FR-011-01, FR-001-06 → FR-011-02, FR-001-13 (waiting periods and demo time scale) →
  FR-011-04, FR-001-15 → FR-011-05, FR-001-17 → FR-011-06, FR-001-14 → FR-011-07. The case clock
  itself stays in FR-001-13.
- **Out of scope**: notice delivery outside the applicant portal, notices in languages other
  than English, the redetermination form's own 30-day window (007).

Story and requirement IDs are not reused. Removed and deferred parts are listed at the end of
the requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the demo in minutes (Priority: P1)

In the demo profile, waits run on a compressed time scale, and a supervisor can jump a case
straight to its next pending deadline.

**Why this priority**: The 3-minute demo shows waits of 15 and 30 days.

**Independent Test**: In the demo profile, put a case into "Awaiting applicant", advance its
clock, and confirm the deadline fires immediately.

**Acceptance Scenarios**:

1. **Given** the demo profile, **When** a supervisor advances a case's clock, **Then** the case's
   next pending timer fires immediately, the case clock jumps to that timer's time, and the
   action is recorded as a demo action.
2. **Given** the normal profile, **When** anyone tries to advance a case's clock, **Then** the
   request is refused.
3. **Given** the demo profile, **When** a case waits, **Then** one day of waiting takes one
   minute, with no code change between profiles.

---

### User Story 2 - Applicant receives the right notice (Priority: P1)

Every decision, and every request the applicant must answer, reaches the applicant's portal as
one of a fixed set of template notices, with caseworker approval where the notice is adverse or
asks the applicant for something. Each determination also gets plain-language explanations.

**Why this priority**: Notices are the only thing applicants receive; a wrong or unapproved
notice is the most visible failure.

**Independent Test**: Decide one case as Approved and one as Denied, and confirm the notice type,
whether it waited for approval, and that explanations are stored with each determination.

**Acceptance Scenarios**:

1. **Given** a case decided as Approved, **When** the decision is recorded, **Then** an approval
   notice from the fixed template is delivered to the applicant's portal without caseworker
   approval.
2. **Given** a denial approved by a caseworker, **When** the approval is recorded, **Then** a
   denial notice built from the fixed template and the applicant explanation is delivered; the
   caseworker approved the outcome and the notice in one action.
3. **Given** a case with missing information, **When** the request for information is produced,
   **Then** it names each missing item and is sent only after a caseworker approves it
   (FR-010-01, "Notice approval").
4. **Given** any determination, **When** it is stored, **Then** the applicant and caseworker
   explanations are built and stored with it.

---

### User Story 3 - Waiting for the applicant (Priority: P2)

When information is missing, the case waits for the applicant's response with a deadline, and
goes to a caseworker if the deadline passes.

**Why this priority**: Missing paperwork is the most common cause of procedural denials.

**Independent Test**: Put a case into "Awaiting applicant", advance the clock past the deadline,
and confirm a caseworker review task appears.

**Acceptance Scenarios**:

1. **Given** an approved request for information, **When** it is sent, **Then** the case moves to
   "Awaiting applicant" with a response deadline 15 days later.
2. **Given** a case awaiting the applicant, **When** the applicant responds, **Then** the case
   runs the income check again with the new information.
3. **Given** a case awaiting the applicant, **When** the deadline passes without a response,
   **Then** a "Missed response deadline" review task is created and the case is not denied
   automatically.

### User Story 4 - Caseworker approves notices (Priority: P1)

A caseworker reviews each adverse notice and each request to the applicant on the case page and
approves it before it reaches the applicant.

**Why this priority**: No adverse notice or request reaches an applicant without approval.

**Independent Test**: In the browser, approve a request for information, then sign in as the
applicant and confirm it appears; confirm an unapproved one does not.

**Acceptance Scenarios**:

1. **Given** a notice awaiting approval, **When** the caseworker approves it, **Then** it is
   delivered to the applicant's portal.
2. **Given** a notice awaiting approval, **When** no caseworker has approved it, **Then** the
   applicant cannot see it.
3. **Given** a favourable template notice (approval or renewal), **When** it is created,
   **Then** it is delivered without approval.

---

### User Story 5 - Applicant reads notices and answers requests (Priority: P1)

An applicant sees the notices delivered to them and any open request for information, with what
is needed and the due date, and responds by uploading documents and confirming details.

**Why this priority**: The request-for-information journey is the core of the demo.

**Independent Test**: In the browser, sign in as the demo applicant with an open request, open the
notice, upload the requested pay stub, and confirm the case leaves "Awaiting applicant".

**Acceptance Scenarios**:

1. **Given** delivered notices, **When** the applicant opens their notices, **Then** each is listed
   with its type and date and can be opened.
2. **Given** an open request for information, **When** the applicant signs in, **Then** they see
   what is needed and the due date, and can respond by uploading documents and confirming
   details; the case then leaves "Awaiting applicant" (FR-011-03).

---

### User Story 6 - Supervisor advances the demo clock (Priority: P1)

In the demo profile, a supervisor presses "Advance clock" on a case page to fire its next pending
wait.

**Why this priority**: The 3-minute demo depends on it (SC-011-01).

**Independent Test**: In the browser with the demo profile on, sign in as a supervisor, advance
the clock on a case awaiting the applicant, and confirm the missed-deadline review task appears;
sign in as a caseworker and confirm there's no button.

**Acceptance Scenarios**:

1. **Given** the demo profile is on and a case has a pending wait, **When** a supervisor presses
   "Advance clock" on the case page, **Then** the wait fires and the history records the demo
   action.
2. **Given** a caseworker, or the demo profile is off, **When** they open a case, **Then** no
   "Advance clock" button is shown.

### Edge Cases

- The applicant responds after the deadline but before a caseworker acts: the response is
  attached and the review task shows it.
- The demo profile is on: every wait follows the compressed time scale, and case history shows
  both simulated and real times (FR-001-13).
- A supervisor advances the clock on a case with no pending timer: the request is refused and
  recorded.
- A case already had its one automatic request for information: further missing information
  goes to a caseworker review instead of a second request.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-011-01**: A request for information MUST give the applicant 15 days to respond, during
  which the case is in "Awaiting applicant".
- **FR-011-02**: When the response deadline passes, the system MUST create a "Missed response
  deadline" review task (FR-010-01) and MUST NOT deny the case automatically.
- **FR-011-03**: When the applicant responds while the case is awaiting them, the case MUST
  run the income check again with the new information. A response that arrives after the
  deadline MUST be attached to the open review task.
- **FR-011-04**: Every waiting period (response windows, review reminders and escalation,
  decision deadline tracking) MUST be configurable, and a demo profile MUST run them on a
  compressed time scale (one day as one minute) without code changes. In the demo profile the
  case clock (FR-001-13) starts at the case's real start time, runs at one day per minute and
  jumps forward when a timer is fired early (FR-011-05).
- **FR-011-05**: In the demo profile only, a supervisor MUST be able to fire a case's next pending
  timer immediately; the action MUST be recorded and MUST be refused outside the demo profile.
- **FR-011-06**: Notices MUST be one of these types, and nothing else is sent to applicants.
  Every notice is built from a fixed template. (Revised: no AI drafts.)

  | Notice | Template filled with | Caseworker approval |
  |---|---|---|
  | Approval | Decision and coverage period | No |
  | Automatic renewal (007) | New coverage period | No |
  | Renewal after response (007) | New coverage period | No |
  | Denial | Decision and applicant explanation | Yes |
  | Coverage ended (007) | Decision and applicant explanation | Yes |
  | Request for information | Missing items (FR-011-12) and due date | Yes |
  | Redetermination form (007) | Items to confirm (FR-007-03) and due date | Yes |

  Approving an adverse outcome and approving its notice are one caseworker action.
- **FR-011-07**: When a determination is stored, the system MUST build the applicant and
  caseworker explanations (FR-004-10) and store them with it. Until 004 is in place, the
  rule-by-rule trace (FR-003-05) is used as the explanation. (Revised: built in the same step;
  no retries.)
- **FR-011-08**: Adverse notices, requests for information and redetermination forms MUST be
  delivered only after a caseworker approves them from the case page. Favourable template
  notices are delivered directly. (Was FR-006-06; revised, editing deferred.)
- **FR-011-09**: Applicants MUST see a list of the notices delivered to them, with type and date,
  and be able to open each one. (Was FR-006-15.)
- **FR-011-10**: When an applicant signs in, the portal MUST show each open request for information
  with what is needed and its due date, and let them respond by uploading documents (FR-002-17)
  and confirming details. (Was FR-006-03, requests part, and FR-006-08, request part.)
- **FR-011-11**: In the demo profile only, supervisors MUST be able to advance a case's clock
  (FR-011-05) from the case page; the button is not shown to other roles or outside the demo
  profile. (Was FR-006-13.)
- **FR-011-12**: When the verification result lists missing information (FR-002-15), the system
  MUST produce a request for information from the fixed template, naming each missing item,
  and hold it for caseworker approval. At most one is produced automatically per case.
  (Replaces FR-002-05 and the drafting in FR-002-12.)

### Removed and deferred

| ID | What it was | Now |
|---|---|---|
| FR-011-06 (AI draft rows) | Request for information and redetermination form drafted by AI | Removed; fixed templates |
| FR-011-07 (retry and fallback), SC-011-04 | Requesting AI explanations, retrying later, falling back to the trace | Removed; explanations are built in the same step |
| FR-011-08 (edit before approving), US4 scenario 2 | Editing a notice and keeping both versions | Deferred; 010's "Edit and approve" action is not offered for notices |

### Key Entities

- **Notice**: type (FR-011-06), content, approval status, delivered time.
- **Timer**: a pending wait on a case (`response_deadline`, `review_reminder`,
  `review_escalation`, and for 007 `redetermination_response_deadline` and `coverage_end`).
  Each has its due time on the case clock, and "Advance clock" fires whichever is due first.
- **Demo action**: a supervisor's advance-clock action, recorded in case history with both
  case-clock and real times.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-011-01**: In the demo profile, one case can be taken from submission through a missed
  deadline to a decision in under 3 minutes using the demo clock.
- **SC-011-02**: 100% of missed response deadlines in testing produce a review task; zero
  automatic denials.
- **SC-011-03**: 100% of notices sent in testing are one of the 7 types in FR-011-06, and 100% of
  adverse notices and requests to the applicant were approved by a caseworker before delivery.

## Assumptions

- The 15-day response window and the 1 day = 1 minute demo time scale are project values (see
  "Project values" in specs/README.md).
- Notices are delivered through the applicant portal only.
- All day counts use calendar days (FR-001-18).
