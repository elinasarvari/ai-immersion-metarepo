# Feature Specification: Case Lifecycle

**Feature Branch**: `feature/001-case-lifecycle`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Durable Medicaid case lifecycle from application to decision with human review"

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: case states, outcomes and transitions; durable progress across restarts; case
  history; the review gate (create a task, wait, resume); the case clock; decision deadline
  tracking; the coverage period for an approved application. Used by 006, 007, 008, 010 and 011.
- **Depends on**: 000 (sign-in, configuration); 002 (document verification), 003
  (determination), 010 (the full set of review reasons and actions) and 011 (notices and
  explanations), each stubbed until ready.
- **Split into 001, 010 and 011** (2026-11-10). 010 Review queue and caseworker actions and 011
  Applicant waits, notices and demo clock now hold the requirements listed under "Moved
  requirements".
- **Out of scope**: appeals, mid-period change reporting, multiple programs, notice delivery
  outside the applicant portal, applicant withdrawal, assigning cases to individual caseworkers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application moves from submission to decision (Priority: P1)

When an applicant submits a Medicaid application, a case is opened and moves through defined
stages (verification, determination, review where needed, decision) until it is decided.

**Why this priority**: This is the backbone every other feature plugs into.

**Independent Test**: Submit applications with stubbed verification and determination and
confirm each reaches the expected outcome through the expected stages. Review tasks are resolved
with "Approve denial" or "Override to approve"; the other actions come with 010.

**Acceptance Scenarios**:

1. **Given** a submitted application, **When** it is received, **Then** exactly one case is opened
   in state "Submitted" with a decision deadline 45 days after receipt.
2. **Given** a verified case, **When** the determination is Eligible, **Then** the case is decided
   as Approved, its coverage period starts (FR-001-22), and the approval notice is requested
   (FR-011-06).
3. **Given** a verified case, **When** the determination is Ineligible, **Then** a review task is
   created, and only after a caseworker approves is the case decided as Denied with its reason
   code and the denial notice requested.
4. **Given** a determination of "Cannot determine", **When** it is returned, **Then** a review task
   is created listing the missing information; the case is never denied automatically.
5. **Given** a case in any state, **When** a transition not allowed from that state is
   requested, **Then** it is refused and recorded as a rejected action.
6. **Given** a household with an open case, **When** a new application is submitted, **Then** it is
   refused with the reason; the same submission sent twice opens one case.

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

### User Story 3 - Deadline visibility (Priority: P3)

Caseworkers can see how close each case is to its 45-day decision deadline.

**Why this priority**: Supports prioritisation and the program metrics.

**Independent Test**: Create cases at different ages and confirm days remaining and the at-risk
flag.

**Acceptance Scenarios**:

1. **Given** a case 36 days old and undecided, **When** its status is viewed, **Then** it shows 9
   days remaining and is flagged at risk.

### Edge Cases

- A caseworker overrides an adverse determination to approve: the case is decided as Approved
  and the override is recorded with its reason; the stored determination is unchanged.
- The income rule and another rule both fail: the reason code is "income over limit".
- The system restarts while a case waits on a review task: the case is still waiting on the same
  task afterwards, and no second task is created.
- The demo profile is on: case history shows both case-clock and real times.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001-01**: The system MUST open exactly one case per submitted application, with a decision
  deadline 45 days after receipt.
- **FR-001-02**: Cases MUST follow defined states (Submitted, Verifying, Awaiting applicant,
  Determining, Under review, Decided) and only allowed transitions.
- **FR-001-03**: Case progress MUST survive system restarts and resume at the same step.
- **FR-001-04**: Retried steps MUST NOT repeat external effects (notices, findings, caseworker
  actions).
- **FR-001-07**: When any component reports that review is needed, the system MUST create a review
  task in the shared caseworker queue and wait for a caseworker action, without holding work
  open while waiting. Review reasons and the actions each allows are in FR-010-01.
- **FR-001-09**: Every adverse determination MUST wait for caseworker approval before the case is
  decided.
- **FR-001-10**: Every state change MUST be recorded in the case history with time, actor and
  reason.
- **FR-001-11**: The system MUST show days remaining to the decision deadline and flag cases
  with 10 or fewer days left as at risk.
- **FR-001-13**: Each case MUST keep a case clock. Outside the demo profile it is the real date;
  in the demo profile it follows the demo time scale (FR-011-04). Every date the case uses
  (deadlines, determination as-of dates, decision dates, history entries) comes from its case
  clock, and history records both case-clock and real times.
- **FR-001-16**: A decided case MUST have one outcome: Approved, or Denied with a reason code
  (income over limit, other rule not met, missing information). When the income rule and another
  rule both fail, the reason code is "income over limit". "Cannot determine" MUST create a
  review task, never a decision.
- **FR-001-18**: All day counts MUST use calendar days.
- **FR-001-20**: When a caseworker overrides a determination, the stored determination MUST stay
  unchanged; the case outcome records the override, the reviewer and the reason.
- **FR-001-22**: An approved new application MUST start a 12-month coverage period on the first
  day of the month its application was received (case clock) and end on the last day of the 12th
  month.
- **FR-001-23**: Submitting the same application twice (same submission reference) MUST open one
  case. A new application MUST be refused, with the reason, while the household has an open case
  or a coverage period that has not ended.

### Moved requirements

IDs are not reused. References elsewhere point to the new IDs.

| Old ID | Now | Topic |
|---|---|---|
| FR-001-05 | FR-011-01 | 15-day response window |
| FR-001-06 | FR-011-02 | Missed response deadline goes to review |
| FR-001-08 | FR-010-02 | Review reminders and escalation |
| FR-001-12 | FR-010-03 | Retry limit goes to review |
| FR-001-13 (part) | FR-011-04 | Configurable waits and demo time scale (the case clock stays in FR-001-13) |
| FR-001-14 | FR-011-07 | Decision explanations |
| FR-001-15 | FR-011-05 | Supervisor advance-clock action |
| FR-001-17 | FR-011-06 | Notice types |
| FR-001-19 | FR-010-01 | Review reasons and actions |
| FR-001-21 | FR-010-04 | One automatic request for information |
| SC-001-04 | SC-011-01 | 3-minute demo journey |

### Key Entities

- **Case**: one application or redetermination for a household; type, state, received date,
  deadline, coverage period, outcome and reason code, history, case clock.
- **Case event**: one entry in the case history (state change, finding, action, demo action) with
  case-clock time, real time, actor and reason.
- **Review task**: a request for a person to act; reason (FR-010-01), evidence, opened time,
  reminder and escalation flags, outcome.
- **Coverage period**: start and end dates and status (active, continued pending review, renewed,
  ended); see FR-001-22 and 007.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001-01**: 100% of cases interrupted by a restart in testing resume correctly, with zero
  duplicate notices or findings.
- **SC-001-02**: 100% of adverse outcomes in testing wait for caseworker approval.
- **SC-001-03**: 100% of "Cannot determine" results in testing produce a review task; zero
  automatic denials.
- **SC-001-05**: A restart test (stop the worker mid-case, restart, confirm no repeated effects)
  and a workflow replay test against recorded case histories pass on every PR.

## Assumptions

- The 45-day decision deadline is a project value for this training build (see "Project values"
  in specs/README.md), modelled on federal Medicaid timeliness rules.
- There is one shared caseworker queue; any caseworker can act on any task.
- Until 010 lands, review tasks offer only "Approve denial" and "Override to approve"; until 011
  lands, notices are recorded as requested but not delivered.
