# Feature Specification: Platform Foundations

**Feature Branch**: `feature/000-platform-foundations`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Platform foundations: configuration, sign-in, errors, health, logging, one-command run"

## Lane & Dependencies

- **Lane**: C (platform and experience)
- **Provides**: sign-in and roles, configuration, error format, health checks, logging, the
  one-command run profiles, AI provider selection. Every other feature depends on this.
- **Depends on**: nothing. Part of the Day 1 contracts PR.
- **Out of scope**: real single sign-on, user self-registration, password reset, cloud
  deployment, multiple environments beyond local development and local production-like.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the whole system with one command (Priority: P1)

A team member clones the project, follows the README and starts every part of the system with
one command, either in development mode or in a production-like mode.

**Why this priority**: Nobody can build or demo anything until the system runs the same way on
every laptop.

**Independent Test**: On a clean machine, follow the README and confirm all components report
healthy.

**Acceptance Scenarios**:

1. **Given** a fresh clone and the documented prerequisites, **When** the developer runs the
   development start command, **Then** every component starts and reports healthy.
2. **Given** a running system, **When** the developer runs the production-like start command,
   **Then** components start with production settings (no auto-reload, built frontend) and
   report healthy.
3. **Given** a running system, **When** the developer runs the reset command, **Then** all data
   is cleared and the synthetic data set is reloaded.

---

### User Story 2 - Sign in with a role (Priority: P1)

An applicant or caseworker signs in with a seeded demo account and only sees what their role
allows.

**Why this priority**: Access control underpins the privacy guarantees in every other feature.

**Independent Test**: Sign in as each demo user and call a protected operation; confirm access
matches the role and unauthenticated calls are refused.

**Acceptance Scenarios**:

1. **Given** a seeded caseworker account, **When** the caseworker signs in, **Then** they receive
   a session that identifies them and their role.
2. **Given** no session, **When** any protected operation is called, **Then** it is refused with
   an "authentication required" error.
3. **Given** an expired session, **When** a protected operation is called, **Then** it is refused
   and the user is asked to sign in again.

---

### User Story 3 - Consistent errors, health and logs (Priority: P2)

Operators see whether each component is healthy, and every failure produces a structured error
for the client and a traceable log entry for the team.

**Why this priority**: Production habit; makes every other feature debuggable.

**Independent Test**: Trigger a validation error and an internal error; check the client
response format and the matching log entry.

**Acceptance Scenarios**:

1. **Given** a request with invalid input, **When** it is processed, **Then** the client gets an
   error with a code, a readable message and the invalid fields, and no internal details.
2. **Given** an unexpected failure, **When** it occurs, **Then** the client gets a generic error
   with a reference ID, and the log entry with the same reference ID holds the details.
3. **Given** a running system, **When** health and readiness are checked, **Then** each component
   reports its own status and the status of what it depends on.

---

### User Story 4 - Switch AI provider by configuration (Priority: P2)

A team member with only Amazon Bedrock access and team members with only Anthropic API access
run the same code by changing configuration alone.

**Why this priority**: The team's access is split across two providers.

**Independent Test**: Run the same AI smoke test with each provider setting and confirm both
succeed without code changes.

**Acceptance Scenarios**:

1. **Given** the provider is set to Anthropic API, **When** the AI smoke test runs, **Then** it
   succeeds using the Anthropic API.
2. **Given** the provider is set to Amazon Bedrock, **When** the same smoke test runs, **Then** it
   succeeds using Bedrock.
3. **Given** an unknown provider value, **When** the system starts, **Then** it refuses to start
   and names the allowed values.

### Edge Cases

- A required setting is missing at startup: the component refuses to start and names the setting.
- A dependency (database, workflow server) is down: readiness reports not ready; health still
  reports the process is alive.
- A log message would include personal data: it is masked before writing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-000-01**: The system MUST start every component with one documented command in
  development mode and one in production-like mode.
- **FR-000-02**: The system MUST provide a command that resets all data and reloads the synthetic
  data set.
- **FR-000-03**: All configuration MUST come from environment settings; an example settings file
  MUST be committed and the real one MUST NOT be.
- **FR-000-04**: The system MUST refuse to start when a required setting is missing or invalid,
  naming the setting.
- **FR-000-05**: The system MUST support three roles: applicant, caseworker and supervisor, with
  seeded demo accounts for each.
- **FR-000-06**: Every operation except health and readiness MUST require a valid, unexpired
  session.
- **FR-000-07**: Sessions MUST expire after a configurable period (default 8 hours).
- **FR-000-08**: Errors returned to clients MUST use one structured format (code, message, field
  details, reference ID) and MUST NOT include stack traces, queries or system details.
- **FR-000-09**: Every component MUST expose health (process alive) and readiness (dependencies
  reachable) checks.
- **FR-000-10**: Logs MUST be structured and include, where known, the case ID, workflow ID and
  request reference ID.
- **FR-000-11**: Logs MUST NOT contain names, addresses, dates of birth, identity numbers or
  document contents.
- **FR-000-12**: The AI model provider MUST be selectable by configuration between the Anthropic
  API and Amazon Bedrock, with no code changes.
- **FR-000-13**: Every outbound call MUST have a timeout and a bounded retry with backoff.
- **FR-000-14**: Every stored record and generated document MUST carry a synthetic-data marker.

### Key Entities

- **User**: a demo account with a role (applicant, caseworker, supervisor); an applicant user is
  linked to one household.
- **Session**: proof of sign-in with user identity, role and expiry.
- **Error**: code, message, field details, reference ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-000-01**: A team member goes from fresh clone to a healthy running system in under 30
  minutes by following the README.
- **SC-000-02**: 100% of protected operations refuse requests without a valid session.
- **SC-000-03**: A secrets scan of every repo finds zero secrets.
- **SC-000-04**: The AI smoke test passes on both providers with no code change.
- **SC-000-05**: Any client error can be traced to its log entry by reference ID in under one
  minute.

## Assumptions

- Demo accounts are seeded; there is no registration or password reset.
- "Production-like" means local processes with production settings, not a deployment.
- Both providers serve the same Claude model family; small output differences are acceptable.
