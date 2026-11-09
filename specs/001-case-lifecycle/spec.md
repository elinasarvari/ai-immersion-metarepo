# Feature Specification: Case Lifecycle

**Feature Branch**: `feature/001-case-lifecycle`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Durable Medicaid case lifecycle from application to decision with human review"

## Lane & Dependencies

- **Lane**: A (workflows and decisions)
- **Provides**: case states, outcomes and transitions; the review-task mechanism; deadline
  tracking; decision notices; the demo clock. Used by 006, 007 and 008.
- **Depends on**: 000 (sign-in, configuration); 002 (document verification), 003 (determination)
  and 004 (explanations), each stubbed until ready.
- **Out of scope**: appeals, mid-period change reporting, multiple programs, notice delivery
  outside the applicant portal, applicant withdrawal, assigning cases to individual caseworkers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application moves from submission to decision (Priority: P1)

When an applicant submits a Medicaid application, a case is opened and moves through defined
stages (verification, determination, review where needed, decision) until it is decided.

**Why this priority**: This is the backbone every other feature plugs into.

**Independent Test**: Submit applications with stubbed verification and determination and
confirm each reaches the expected outcome through the expected stages.

**Acceptance Scenarios**:

1. **Given** a submitted application, **When** it is received, **Then** exactly one case is opened
   in state "Submitted" with a decision deadline 45 days after receipt.
2. **Given** a verified case, **When** the determination is Eligible, **Then** the case is decided
   as Approved, a favourable notice from the fixed template is delivered to the applicant's
   portal, and explanations are requested.
3. **Given** a verified case, **When** the determination is Ineligible, **Then** a review task is
   created, and only after a caseworker approves is the case decided as Denied with its reason
   code and the adverse notice delivered.
4. **Given** a determination of "Cannot determine", **When** it is returned, **Then** a review task
   is created listing the missing information; the case is never denied automatically.
5. **Given** a case in any state, **When** a transition not allowed from that state is
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
goes to a caseworker if the deadline passes.

**Why this priority**: Missing paperwork is the most common cause of procedural denials.

**Independent Test**: Put a case into "Awaiting applicant", advance the clock past the deadline,
and confirm a caseworker review task appears.

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
verification, a missed deadline, a case that cannot be determined) a review task is placed in
the shared caseworker queue and the case waits until a caseworker acts.

**Why this priority**: Human control over adverse outcomes is a core principle.

**Independent Test**: Trigger each review reason and confirm a task is created, the case waits,
and the caseworker's action resumes it.

**Acceptance Scenarios**:

1. **Given** a component reports that review is needed, **When** the report arrives, **Then** a
   review task is created in the shared queue with its reason and evidence, and the case waits.
2. **Given** an open review task, **When** a caseworker approves, edits or overrides with a
   reason, **Then** the case resumes accordingly and the action is recorded.
3. **Given** a review task open for 2 days, **When** that time passes, **Then** caseworkers are
   reminded; at 4 days the task is flagged as escalated for supervisors.
4. **Given** the same caseworker action submitted twice, **When** both arrive, **Then** it is
   applied once.

---

### User Story 5 - Run the demo in minutes (Priority: P1)

In the demo profile, waits run on a compressed time scale, and a supervisor can jump a case
straight to its next pending deadline.

**Why this priority**: The 3-minute demo shows waits of 15 and 30 days.

**Independent Test**: In the demo profile, put a case into "Awaiting applicant", advance its
clock, and confirm the deadline fires immediately.

**Acceptance Scenarios**:

1. **Given** the demo profile, **When** a supervisor advances a case's clock, **Then** the case's
   next pending timer fires immediately and the action is recorded as a demo action.
2. **Given** the normal profile, **When** anyone tries to advance a case's clock, **Then** the
   request is refused.

---

### User Story 6 - Deadline visibility (Priority: P3)

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
- A caseworker overrides an adverse determination to approve: the case is decided as Approved
  and the override is recorded with its reason.
- The AI provider is down when explanations are requested: the decision is not delayed; the
  explanations are generated when the provider is back.
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
  task in the shared caseworker queue and wait for a caseworker action, without holding work
  open while waiting.
- **FR-001-08**: If a review task is not actioned within 2 days, the system MUST remind
  caseworkers; after 4 days it MUST flag the task as escalated for supervisors.
- **FR-001-09**: Every adverse determination MUST wait for caseworker approval before the case is
  decided.
- **FR-001-10**: Every state change MUST be recorded in the case history with time, actor and
  reason.
- **FR-001-11**: The system MUST show days remaining to the decision deadline and flag cases
  with 10 or fewer days left as at risk.
- **FR-001-12**: When verification or determination fails after its retry limit (3 attempts),
  the system MUST create a review task instead of stalling.
- **FR-001-13**: Every waiting period (response windows, review reminders and escalation,
  decision deadline tracking) MUST be configurable, and a demo profile MUST run them on a
  compressed time scale (one day as one minute) without code changes.
- **FR-001-14**: After every determination, the system MUST request the applicant and
  caseworker explanations (004) and store them with the determination; if the request fails,
  it MUST retry later without delaying the decision.
- **FR-001-15**: In the demo profile only, a supervisor MUST be able to fire a case's next pending
  timer immediately; the action MUST be recorded and MUST be refused outside the demo profile.
- **FR-001-16**: A decided case MUST have one outcome: Approved, or Denied with a reason code
  (income over limit, other rule not met, missing information). "Cannot determine" MUST create a
  review task, never a decision.
- **FR-001-17**: Favourable decision notices MUST be built from a fixed template and delivered
  without approval; adverse notices MUST include the applicant explanation and be delivered only
  after caseworker approval.
- **FR-001-18**: All day counts MUST use calendar days.

### Key Entities

- **Case**: one application or redetermination for a household; type, state, received date,
  deadline, coverage period, outcome and reason code, history.
- **Case event**: one entry in the case history (state change, finding, action, demo action) with
  time, actor and reason.
- **Review task**: a request for a person to act; reason, evidence, opened time, escalation flag,
  outcome.
- **Caseworker action**: approve, edit or override, with reviewer, time and reason.
- **Decision notice**: favourable (template) or adverse (template plus explanation), approval
  status, delivered time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001-01**: 100% of cases interrupted by a restart in testing resume correctly, with zero
  duplicate notices or findings.
- **SC-001-02**: 100% of adverse outcomes in testing wait for caseworker approval.
- **SC-001-03**: 100% of missed response deadlines and "Cannot determine" results produce a review
  task; zero automatic denials.
- **SC-001-04**: In the demo profile, one case can be taken from submission through a missed
  deadline to a decision in under 3 minutes using the demo clock.

## Assumptions

- The 45-day decision deadline and 15-day response window are project values for this training
  build (see "Project values" in specs/README.md), modelled on federal Medicaid timeliness rules.
- There is one shared caseworker queue; any caseworker can act on any task.
- Notices are delivered through the applicant portal only.
