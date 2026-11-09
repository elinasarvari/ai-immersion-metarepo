# Feature Specification: Agent Tool Access

**Feature Branch**: `feature/005-agent-tool-access`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Controlled tools that AI agents use to reach case data, documents and verification sources"

## Lane & Dependencies

- **Lane**: B (AI and knowledge)
- **Provides**: the set of tools AI agents use to read case data and documents, record findings,
  draft requests for information, check simulated verification sources and search policy. Used
  by 002 and 007.
- **Depends on**: 000 (sign-in, configuration, logging), 003 (data set), 004 (policy search).
- **Out of scope**: real external verification services; tools that make eligibility decisions;
  tools that send notices directly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agents read what they need for one case (Priority: P1)

An agent working on a case can read the case summary, household, case history and documents,
and save its extractions and findings.

**Why this priority**: Verification cannot work without data access.

**Independent Test**: Call each tool for a seeded case and confirm the expected data comes back
in the agreed shape.

**Acceptance Scenarios**:

1. **Given** a case being processed, **When** an agent requests the case summary, household,
   history or documents, **Then** it receives them in the agreed format.
2. **Given** an agent saves an extraction or finding, **When** it saves the same one again,
   **Then** only one copy is stored.
3. **Given** an agent drafts a request for information, **When** the draft is saved, **Then** it
   is stored as awaiting approval and is not sent.

---

### User Story 2 - Access limited to the case in hand (Priority: P1)

Tools only return data for the case the agent is working on.

**Why this priority**: Least privilege; protects other households' data.

**Independent Test**: Ask a tool for another household's data during a case and confirm refusal.

**Acceptance Scenarios**:

1. **Given** an agent working on case A, **When** it requests data for case B, **Then** the request
   is refused and logged.
2. **Given** a request with missing or invalid inputs, **When** it is made, **Then** it is refused
   with a clear error naming the problem.

---

### User Story 3 - Realistic simulated verification sources (Priority: P2)

Agents can check income and identity against simulated external sources that behave like real
ones: variable response times, occasional failures and timeouts.

**Why this priority**: Exercises retry and failure handling as in production.

**Independent Test**: Call the simulated sources many times and confirm latency and failure rates
match configuration.

**Acceptance Scenarios**:

1. **Given** default settings, **When** income is verified 100 times, **Then** response times vary
   between 0.5 and 3 seconds and about 5% of calls fail.
2. **Given** a simulated source that does not respond, **When** the call times out, **Then** a
   clear timeout error is returned.

---

### User Story 4 - Every tool call is audited (Priority: P2)

Every tool call is recorded so the team can see what an agent did on a case.

**Why this priority**: Traceability of AI behaviour.

**Independent Test**: Process a case and confirm every tool call appears in the audit record.

**Acceptance Scenarios**:

1. **Given** a processed case, **When** its tool calls are reviewed, **Then** each shows tool name,
   case, outcome and duration, with no personal data.

### Edge Cases

- A document is very large: it is returned in parts, with a clear indicator of how many remain.
- The verification source returns a result for a different person: returned as a mismatch, not
  silently accepted.
- A tool is called after the case is decided: read tools work; write tools are refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-005-01**: The system MUST provide tools to: read the case summary, read the household,
  read the case history, list documents, read a document, save an extraction, record a finding,
  draft a request for information, verify income, verify identity and search policy.
- **FR-005-02**: Every tool MUST have a defined input and output format, and MUST refuse invalid
  input with an error naming the problem.
- **FR-005-03**: Tools MUST return or change data only for the case the agent is processing;
  any other request MUST be refused and logged.
- **FR-005-04**: Read tools MUST NOT change data.
- **FR-005-05**: Saving the same extraction or finding twice MUST store it once.
- **FR-005-06**: Drafting a request for information MUST store it as awaiting approval and MUST
  NOT send it.
- **FR-005-07**: Simulated verification sources MUST have configurable response time (default
  0.5–3 seconds) and failure rate (default 5%), and MUST time out after a configurable limit
  (default 10 seconds).
- **FR-005-08**: Every tool call MUST be recorded with tool name, case, outcome and duration, and
  without personal data.
- **FR-005-09**: Write tools MUST be refused for decided cases.

### Key Entities

- **Tool**: a named capability with an input format, output format and access rule.
- **Tool call record**: tool, case, time, outcome, duration.
- **Verification response**: source, match result, confidence, response time, or error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-005-01**: 100% of cross-case access attempts in testing are refused and logged.
- **SC-005-02**: 100% of tool calls during a processed case appear in the audit record.
- **SC-005-03**: Simulated failure and latency rates fall within 2 percentage points and 10% of
  configuration over 1,000 calls, with delays scaled down for the test.
- **SC-005-04**: Zero personal data found in tool call records.

## Assumptions

- Agents always work on exactly one case at a time.
- Simulated sources draw their answers from the synthetic data set (003).
