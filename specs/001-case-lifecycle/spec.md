# Feature Specification: Case Lifecycle

**Feature Branch**: `feature/001-case-lifecycle`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Durable Medicaid case lifecycle from application to decision with human review"

## Lane & Dependencies

- **Lane**: A (workflows and decisions)
- **Provides**: case states and transitions, the review-task mechanism, deadline tracking,
  caseworker actions as resumable events. Used by 002, 006, 007 and 008.
- **Depends on**: 000 (sign-in, configuration); 002 (document verification, stubbed until
  ready); 003 (determination, stubbed until ready).
- **Out of scope**: appeals, mid-period change reporting, multiple programs, notice delivery
  outside the applicant portal, applicant withdrawal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application moves from submission to decision (Priority: P1)

When an applicant submits a Medicaid application, a case is opened and moves through defined
stages (verification, determination, review, decision) until it is decided.

**Why this priority**: This is the backbone every other feature plugs into.

**Independent Test**: Submit an application with stubbed verification and determination and
confirm the case reaches "Decided" through the expected stages.

**Acceptance Scenarios**:

1. **Given** a submitted application, **When** it is received, **Then** exactly one case is opened
   in state "Submitted" with a decision deadline 45 days after receipt.
2. **Given** a case with verified documents, **When** the determination is approved, **Then** the
   case moves to "Decided" and the decision is recorded in the case history.
3. **Given** a case in any state, **When** a transition not allowed from that state is
   requested, **Then** it is refused and recorded as a rejected action.

---

### User Story 2 - Case survives restarts (Priority: P1)

If the system stops in the middle of a case, the case resumes exactly where it was after a
restart, with no step repeated.

**Why this priority**: This is the durability guarantee at the centre of the demo.

**Independent Test**: Stop the system mid-verification, restart it, and confirm the case
continues without repeating completed steps or sending duplicate notices.

**Acceptance Scenarios**:

1. **Given** a case mid-verification, **When** the system restarts, **Then** the case continues
   from the same step.
2. **Given** a notice already sent, **When** the step that sent it is retried, **Then** no second
   notice is sent.

---

### User Story 3 - Waiting for the applicant (Priority: P2)

When information is missing, the case waits for the applicant's response with a deadline, and
escalates to a caseworker if the deadline passes.

**Why this priority**: Missing paperwork is the most common cause of procedural denials.

**Independent Test**: Put a case into "Awaiting applicant", move time past the response
deadline, and confirm a caseworker review task appears.

**Acceptance Scenarios**:

1. **Given** an approved request for information, **When** it is sent, **Then** the case moves to
   "Awaiting applicant" with a response deadline 15 days later.
2. **Given** a case awaiting the applicant, **When** the applicant responds, **Then** the case
   resumes verification with the new information.
3. **Given** a case awaiting the applicant, **When** the deadline passes without a response,
   **Then** a caseworker review task is created and the case is not denied automatically.

---

### User Story 4 - Human review tasks (Priority: P2)

Whenever the case needs a person (an adverse decision, a notice to approve, a stuck
verification, a missed deadline) a review task is created and the case waits until a
caseworker acts.

**Why this priority**: Human control over adverse outcomes is a core principle.

**Independent Test**: Trigger each review reason and confirm a task is created, the case waits,
and the caseworker's action resumes it.

**Acceptance Scenarios**:

1. **Given** a component reports that review is needed, **When** the report arrives, **Then** a
   review task is created with its reason, evidence and deadline, and the case waits.
2. **Given** an open review task, **When** a caseworker approves, edits or overrides with a
   reason, **Then** the case resumes accordingly and the action is recorded.
3. **Given** a review task open for 2 business days, **When** that time passes, **Then** the
   assigned caseworker is reminded; at 4 business days the task is reassigned to a supervisor.
4. **Given** the same caseworker action submitted twice, **When** both arrive, **Then** it is
   applied once.

---

### User Story 5 - Deadline visibility (Priority: P3)

Caseworkers can see how close each case is to its 45-day decision deadline.

**Why this priority**: Supports prioritisation and the program metrics.

**Independent Test**: Create cases at different ages and confirm days remaining and the at-risk
flag.

**Acceptance Scenarios**:

1. **Given** a case 36 days old and undecided, **When** its status is viewed, **Then** it shows 9
   days remaining and is flagged at risk.

### Edge Cases

- The applicant responds after the deadline but before a caseworker acts: the response is
  attached and the review task shows it.
- Verification or determination fails repeatedly: after the retry limit, a review task is
  created instead of the case stalling.
- A caseworker overrides an adverse decision to approve: the case is decided as approved and the
  override is recorded with its reason.
- Deadlines that land on a weekend or state holiday: business-day counting skips them.
- The demo profile is on: every wait follows the compressed time scale, and case history shows
  both simulated and real times.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001-01**: The system MUST open exactly one case per submitted application, with a decision
  deadline 45 days after receipt.
- **FR-001-02**: Cases MUST follow defined states (Submitted, Verifying, Awaiting applicant,
  Determining, Under review, Decided) and only allowed transitions.
- **FR-001-03**: Case progress MUST survive system restarts and resume at the same step.
- **FR-001-04**: Retried steps MUST NOT repeat external effects (notices, findings, caseworker
  actions).
- **FR-001-05**: A request for information MUST give the applicant 15 days to respond.
- **FR-001-06**: When the response deadline passes, the system MUST create a caseworker review
  task and MUST NOT deny the case automatically.
- **FR-001-07**: When any component reports that review is needed, the system MUST create a review
  task and wait for a caseworker action, without holding work open while waiting.
- **FR-001-08**: If a review task is not actioned within 2 business days, the system MUST remind
  the assigned caseworker; after 4 business days it MUST reassign the task to a supervisor.
- **FR-001-09**: Every adverse determination MUST wait for caseworker approval before the case is
  decided.
- **FR-001-10**: Every state change MUST be recorded in the case history with time, actor and
  reason.
- **FR-001-11**: The system MUST show days remaining to the decision deadline and flag cases
  with 10 or fewer days left as at risk.
- **FR-001-12**: When verification or determination fails after its retry limit, the system MUST
  create a review task instead of stalling.
- **FR-001-13**: Every waiting period (response windows, review reminders and reassignment,
  decision deadline tracking) MUST be configurable, and a demo profile MUST run them on a
  compressed time scale (for example one day as one minute) without code changes.

### Key Entities

- **Case**: one application or redetermination for a household; state, received date, deadline,
  coverage period, history.
- **Case event**: one entry in the case history (state change, finding, action) with time, actor
  and reason.
- **Review task**: a request for a person to act; reason, evidence, assignee, deadline, outcome.
- **Caseworker action**: approve, edit or override, with reviewer, time and reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001-01**: 100% of cases interrupted by a restart in testing resume correctly, with zero
  duplicate notices or findings.
- **SC-001-02**: 100% of adverse outcomes in testing wait for caseworker approval.
- **SC-001-03**: 100% of missed response deadlines produce a review task; zero automatic denials.
- **SC-001-04**: A full case can be demonstrated end to end, with deadlines simulated, in under
  5 minutes.

## Assumptions

- The 45-day decision deadline follows federal Medicaid timeliness rules for non-disability
  applications.
- The 15-day response window is based on our reading of federal Medicaid rules (42 CFR Part 435);
  the team should confirm it against the current regulation before the demo.
- Business days exclude weekends and Illinois state holidays for the demo year.
- Notices are delivered through the applicant portal only.
