# Feature Specification: Applicant Waits, Notices and Demo Clock

**Feature Branch**: `feature/011-applicant-waits-notices`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Split of 001 case lifecycle: applicant waits, notices and demo clock. Waiting for the applicant with a response deadline, configurable waiting periods with a compressed demo time scale, the notice catalogue, and decision explanations."

## Lane & Dependencies

- **Lane**: Workflows
- **Provides**: the "Awaiting applicant" wait and its response deadline; configurable waiting
  periods and the demo time scale; the supervisor "advance clock" action; the catalogue of
  notices sent to applicants; requesting and storing decision explanations. Used by 006, 007 and
  008.
- **Depends on**: 001 (cases, states, case history, the case clock); 010 (review reasons and
  actions); 000 (configuration profiles, supervisor role); 002 (AI-drafted notices), 003 (the
  rule-by-rule trace, FR-003-05) and 004 (explanations), each stubbed until ready.
- **Split from**: 001 Case lifecycle (2026-11-10). Old IDs map to new ones: FR-001-05 →
  FR-011-01, FR-001-06 → FR-011-02, FR-001-13 (waiting periods and demo time scale) →
  FR-011-04, FR-001-15 → FR-011-05, FR-001-17 → FR-011-06, FR-001-14 → FR-011-07. The case clock
  itself stays in FR-001-13.
- **Out of scope**: notice delivery outside the applicant portal, notices in languages other
  than English, the redetermination form's own 30-day window (007), the screens that show
  notices and the advance-clock button (006).

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
one of a fixed set of notices, with caseworker approval where the notice is adverse or
AI-drafted. Each determination also gets plain-language explanations.

**Why this priority**: Notices are the only thing applicants receive; a wrong or unapproved
notice is the most visible failure.

**Independent Test**: Decide one case as Approved and one as Denied with stubbed explanations,
and confirm the notice type, its content source, whether it waited for approval, and that
explanations are stored with each determination.

**Acceptance Scenarios**:

1. **Given** a case decided as Approved, **When** the decision is recorded, **Then** an approval
   notice from the fixed template is delivered to the applicant's portal without caseworker
   approval.
2. **Given** a denial approved by a caseworker, **When** the approval is recorded, **Then** a
   denial notice built from the fixed template and the applicant explanation is delivered; the
   caseworker approved the outcome and the notice in one action.
3. **Given** an AI-drafted request for information, **When** it is ready, **Then** it is sent only
   after a caseworker approves it (FR-010-01, "Notice approval").
4. **Given** any determination, **When** it is stored, **Then** the applicant and caseworker
   explanations are requested and stored with it.

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
   **Then** a "Missed response deadline" review task is created and the case is not denied
   automatically.

### Edge Cases

- The applicant responds after the deadline but before a caseworker acts: the response is
  attached and the review task shows it.
- The AI provider is down when explanations are requested: the decision is not delayed; the
  explanations are generated when the provider is back.
- The applicant explanation is still unavailable after the retry limit for a denial: the notice
  uses the rule-by-rule trace (FR-003-05) and the review task says so.
- The demo profile is on: every wait follows the compressed time scale, and case history shows
  both simulated and real times (FR-001-13).
- A supervisor advances the clock on a case with no pending timer: the request is refused and
  recorded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-011-01**: A request for information MUST give the applicant 15 days to respond, during
  which the case is in "Awaiting applicant".
- **FR-011-02**: When the response deadline passes, the system MUST create a "Missed response
  deadline" review task (FR-010-01) and MUST NOT deny the case automatically.
- **FR-011-03**: When the applicant responds while the case is awaiting them, the case MUST
  resume verification with the new information. A response that arrives after the deadline
  MUST be attached to the open review task.
- **FR-011-04**: Every waiting period (response windows, review reminders and escalation,
  decision deadline tracking) MUST be configurable, and a demo profile MUST run them on a
  compressed time scale (one day as one minute) without code changes. In the demo profile the
  case clock (FR-001-13) starts at the case's real start time, runs at one day per minute and
  jumps forward when a timer is fired early (FR-011-05).
- **FR-011-05**: In the demo profile only, a supervisor MUST be able to fire a case's next pending
  timer immediately; the action MUST be recorded and MUST be refused outside the demo profile.
- **FR-011-06**: Notices MUST be one of these types, and nothing else is sent to applicants:

  | Notice | Built from | Caseworker approval |
  |---|---|---|
  | Approval | Fixed template | No |
  | Automatic renewal (007) | Fixed template | No |
  | Renewal after response (007) | Fixed template | No |
  | Denial | Fixed template + applicant explanation | Yes |
  | Coverage ended (007) | Fixed template + applicant explanation | Yes |
  | Request for information | AI draft (002) | Yes |
  | Redetermination form (007) | AI draft (002) | Yes |

  Approving an adverse outcome and approving its notice are one caseworker action.
- **FR-011-07**: After every determination, the system MUST request the applicant and
  caseworker explanations (004) and store them with the determination; if the request fails,
  it MUST retry later without delaying the decision. An adverse notice waits for the applicant
  explanation; if it is still unavailable after the retry limit, the notice uses the
  rule-by-rule trace (FR-003-05) as its explanation and the review task says so.

### Key Entities

- **Notice**: type (FR-011-06), content, approval status, original and edited versions,
  delivered time.
- **Timer**: a pending wait on a case (response deadline, review reminder, review escalation,
  redetermination start), with its due time on the case clock.
- **Demo action**: a supervisor's advance-clock action, recorded in case history with both
  case-clock and real times.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-011-01**: In the demo profile, one case can be taken from submission through a missed
  deadline to a decision in under 3 minutes using the demo clock.
- **SC-011-02**: 100% of missed response deadlines in testing produce a review task; zero
  automatic denials.
- **SC-011-03**: 100% of notices sent in testing are one of the 7 types in FR-011-06, and 100% of
  adverse and AI-drafted notices were approved by a caseworker before delivery.
- **SC-011-04**: Zero decisions in testing are delayed by a failed explanation request.

## Assumptions

- The 15-day response window and the 1 day = 1 minute demo time scale are project values (see
  "Project values" in specs/README.md).
- Notices are delivered through the applicant portal only.
- All day counts use calendar days (FR-001-18).
