# Feature Specification: Review Queue and Caseworker Actions

**Feature Branch**: `feature/010-review-queue`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Split of 001 case lifecycle: review queue and caseworker actions. Every review reason, the actions each allows, reminders and escalation, and the fallback to review when automated steps keep failing."

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: the full set of review reasons and the actions each one allows (FR-010-01);
  reminders and escalation for open tasks; the fallback to review when verification or
  determination keeps failing; the limit on automatic requests for information; the review queue
  and task screens. Used by 007, 008 and 011.
- **Depends on**: 001 (cases, the review gate, case history, the case clock, the case page); 002 (verification
  findings and drafted requests for information), 004 (explanation checks) and 007 (missed
  redetermination deadlines, coverage end dates), each stubbed until ready.
- **Split from**: 001 Case lifecycle (2026-11-10). Old IDs map to new ones: FR-001-19 →
  FR-010-01, FR-001-08 → FR-010-02, FR-001-12 → FR-010-03, FR-001-21 → FR-010-04.
- **Out of scope**: assigning tasks to individual caseworkers, notifications by email or text,
  supervisor-only queues, timing of the applicant's response window (011).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Caseworker resolves a review task (Priority: P2)

Whenever a case needs a person (an adverse decision, a notice to approve, a doubtful
verification, a missed deadline, a case that cannot be determined, an explanation that failed
its checks) a review task with its reason and evidence is placed in the shared caseworker queue.
The caseworker picks one of the actions that reason allows, and the case resumes accordingly.

**Why this priority**: Human control over adverse outcomes and AI output is a core principle.
001 provides the basic gate (create a task, wait, resume); this story gives every reason its
proper actions.

**Independent Test**: Raise each of the six review reasons against a case, confirm the task
offers exactly the actions in FR-010-01, take each action, and confirm the result and the
recorded action.

**Acceptance Scenarios**:

1. **Given** a component reports that review is needed, **When** the report arrives, **Then** a
   review task is created in the shared queue with one reason from FR-010-01 and its evidence,
   and the case waits.
2. **Given** an open review task, **When** a caseworker takes an action its reason allows,
   **Then** the case resumes with the result listed for that action and the action is recorded
   with reviewer, time and reason.
3. **Given** an open review task, **When** a caseworker requests an action its reason does not
   allow, **Then** the request is refused and recorded as a rejected action.
4. **Given** an action marked * in FR-010-01, **When** it is submitted without a reason, **Then**
   it is refused.
5. **Given** the same caseworker action submitted twice, **When** both arrive, **Then** it is
   applied once.

---

### User Story 2 - Stuck work goes to a person (Priority: P2)

When verification or determination keeps failing, the case goes to a caseworker instead of
stalling.

**Why this priority**: A case that stalls silently misses its decision deadline.

**Independent Test**: Make the stubbed verification fail on every attempt and confirm that after
the third attempt a "Verification review" task appears; repeat for determination.

**Acceptance Scenarios**:

1. **Given** verification fails, **When** it has failed 3 times, **Then** a "Verification review"
   task is created with the cause "retry limit reached".
2. **Given** determination fails, **When** it has failed 3 times, **Then** a review task is
   created and the case does not stall.

---

### User Story 3 - Overdue tasks are reminded and escalated (Priority: P2)

Tasks that sit in the queue too long are marked so caseworkers and supervisors can see them.

**Why this priority**: Supports the decision deadline and the supervisor view. The escalation
flag is the third item to cut if behind (specs/README.md); the reminder is kept.

**Independent Test**: Open a review task, advance the case clock by 2 days and then by 4 days,
and confirm the reminder and then the escalated flag.

**Acceptance Scenarios**:

1. **Given** a review task open for 2 days, **When** that time passes, **Then** the task is
   marked "reminder" in the queue.
2. **Given** a review task open for 4 days, **When** that time passes, **Then** the task is
   flagged as escalated for supervisors.
3. **Given** a redetermination review task open when the household's coverage end date passes,
   **When** that date passes, **Then** the task is flagged as escalated.

### User Story 4 - Caseworker works the review queue (Priority: P1)

A caseworker sees the open review tasks in one shared queue ordered by deadline, opens one, sees
its reason and evidence, and takes one of the actions that reason allows.

**Why this priority**: This is how human control actually happens.

**Independent Test**: In the browser, with seeded review tasks of every reason, sign in as a
caseworker, act on each task type and confirm the case resumes; sign in as a supervisor and filter
to escalated tasks.

**Acceptance Scenarios**:

1. **Given** open review tasks, **When** the caseworker opens the queue, **Then** tasks are listed
   by soonest decision deadline (redeterminations, which have none, by coverage end date), showing
   reason, days remaining or coverage end date, at-risk status, and reminder and escalation
   flags.
2. **Given** an open task, **When** the caseworker opens it, **Then** they see its reason and
   evidence and only the actions the reason allows, and actions marked * ask for a reason.
3. **Given** a task already actioned, **When** a second caseworker tries to act on it, **Then** the
   action is refused with who acted and when.
4. **Given** a task open for 4 days, **When** a supervisor filters the queue to escalated tasks,
   **Then** it is listed, showing how long it has been open.

### Edge Cases

- A caseworker overrides an adverse determination to approve: the case is decided as Approved
  and the override is recorded with its reason (FR-001-20).
- A task is actioned at the moment its reminder fires: the action wins; the reminder flag is not
  set on a closed task.
- A "Request information" action when the case has already had its one automatic request: the
  request is still drafted, because it is a caseworker action (FR-010-04).
- "Extend by 15 days" chosen a second time for the same request: refused (once per request).
- Two caseworkers open the same task: the second action is refused with "already actioned by …".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-010-01**: Every review task MUST have one of these reasons, and offer only the actions
  listed for it. Every action is recorded (FR-001-10) and needs a reason when marked *.

  | Reason | Raised when | Actions and result |
  |---|---|---|
  | Adverse determination | Determination is Ineligible | Approve denial → Decided, Denied (notice delivered); Override to approve* → Decided, Approved; Request information → request drafted (002) |
  | Cannot determine | Determination is Cannot determine | Request information → request drafted listing the missing items; Correct a value* → determined again |
  | Notice approval | An AI-drafted notice is ready | Approve → sent; Edit and approve → edited version sent, both kept |
  | Verification review | Low confidence, unreadable document, different person, identity or income source mismatch, missing citation, verification unavailable, or retry limit reached (002, FR-010-03) | Accept findings → Determining; Correct a value* → Determining with the corrected value; Dismiss a finding* → Determining without it; Request information → request drafted |
  | Missed response deadline | A response window ends with no response (FR-011-02, FR-007-04) | Deny for missing information → Decided, Denied (for a redetermination: coverage ended by caseworker decision); Extend by 15 days* (once per request) → Awaiting applicant; Continue with held data* → Determining |
  | Explanation review | An explanation fails its checks (FR-004-11) | Approve as is; Edit and approve. Does not block the decision. |

  Correcting a value and dismissing a finding both count as overrides of AI output (FR-002-11,
  FR-002-19).
- **FR-010-02**: If a review task is not actioned within 2 days, the system MUST remind
  caseworkers by marking the task "reminder" in the queue (there are no email or text
  notifications); after 4 days, or when a household's coverage end date passes while its
  redetermination review is open (FR-007-04), it MUST flag the task as escalated for supervisors.
- **FR-010-03**: When verification or determination fails after its retry limit (3 attempts),
  the system MUST create a review task instead of stalling.
- **FR-010-04**: The system MUST draft at most one request for information automatically per case.
  Any further request is made only by a caseworker action from a review task.
- **FR-010-05**: An action that the task's reason does not allow, or a * action without a reason,
  MUST be refused and recorded as a rejected action.
- **FR-010-06**: A caseworker action submitted more than once for the same task MUST be applied
  once.
- **FR-010-07**: The caseworker console MUST show one shared review queue of open tasks sorted by
  decision deadline (redeterminations by coverage end date), showing reason, days remaining or
  coverage end date, at-risk status, and the reminder and escalation flags (FR-010-02).
  Supervisors can filter it to escalated tasks. (Was FR-006-01.)
- **FR-010-08**: A task screen MUST show the task's reason and evidence and offer only the actions
  its reason allows (FR-010-01), asking for a reason where one is required (FR-010-05). A task
  already actioned MUST refuse further actions and say who acted. (Was FR-006-01 and
  FR-006-12.)

### Key Entities

- **Review task**: a request for a person to act; reason (FR-010-01), evidence, opened time,
  reminder and escalation flags, outcome. Shape defined in 001.
- **Caseworker action**: one of the actions in FR-010-01, with reviewer, time and reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-010-01**: For each of the 6 review reasons, 100% of tasks in testing offer exactly the
  actions in FR-010-01, and every allowed action produces its listed result.
- **SC-010-02**: 100% of verification and determination failures that reach the retry limit in
  testing produce a review task; zero cases stall.
- **SC-010-03**: 100% of tasks left open past 2 and 4 days (case clock) in testing carry the
  reminder and escalated flags respectively.
- **SC-010-04**: Zero caseworker actions are applied twice in testing.
- **SC-010-05**: A caseworker completes a review in the browser (open, read the evidence, act) in
  under 2 minutes. (Was SC-006-01.)

## Assumptions

- There is one shared caseworker queue; any caseworker can act on any task.
- Reminder and escalation times run on the case clock (FR-001-13) and follow the demo time scale
  in the demo profile (FR-011-04).
- The 2-day reminder and 4-day escalation are project values (see "Project values" in
  specs/README.md).
