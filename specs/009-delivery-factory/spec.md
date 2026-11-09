# Feature Specification: Delivery Factory and Demo Readiness

**Feature Branch**: `feature/009-delivery-factory`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Software factory, traceability, quality dashboard and demo reliability"

## Lane & Dependencies

- **Lane**: Platform & UI
- **Provides**: the setup of both code repos, the process check on every pull request, the
  requirement traceability report, the factory metrics, the quality dashboard shown in the demo,
  and the demo controls (reset to a known start, recorded AI responses, demo script). This is the
  "software factory" half of the Day 3 demo.
- **Depends on**: 000 (CI pipeline, run commands), every other feature's tests and evaluation
  results (read only). The repo setup (US1) is part of the Day 1 contracts PR.
- **Target repos**: `repos/benefit-be` and `repos/benefit-fe` (repo setup, CI checks), and the
  metarepo `scripts/factory/` and `templates/` (reports that read `specs/` across both repos).
- **Out of scope**: hosted dashboards, metrics stored outside git and GitHub, measuring
  individual people, changes to the Spec Kit templates or scripts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Both code repos follow the factory from the first commit (Priority: P1)

Each code repo is set up on Day 1 morning so that every later change goes through the same
process: agent instructions that point at the shared rules, a pull request template, required
checks and a protected main branch.

**Why this priority**: The factory only works if it is in place before the first feature
branch. Adding it later means re-checking work that has already merged.

**Independent Test**: Clone each repo, run the setup check, open a pull request without the
required sections and confirm it is blocked.

**Acceptance Scenarios**:

1. **Given** a fresh clone of either code repo, **When** a team member opens it in Claude Code or
   Copilot, **Then** the agent instructions point at the rule sets for that repo's paths.
2. **Given** the main branch, **When** anyone tries to push to it directly or merge without
   passing checks and one approving review, **Then** it is refused.
3. **Given** a laptop missing a required tool, **When** the setup check runs, **Then** it names
   each missing tool and how to install it.

---

### User Story 2 - Every pull request proves it followed the process (Priority: P1)

Every pull request states which requirements it covers and the result of each lane review its
changes need. A check fails the pull request when either is missing or a review did not pass.

**Why this priority**: Lane reviews are the factory's quality gate; without a check they are a
convention nobody can show was followed.

**Independent Test**: Open pull requests that (a) omit requirement IDs, (b) change a lane's
folders without that lane's review result, (c) report a FAIL; confirm each is blocked with a
message naming the problem.

**Acceptance Scenarios**:

1. **Given** a pull request that changes files in a lane's folders, **When** checks run, **Then**
   the check requires a review result for that lane (from the ownership table in
   `project-rules/backend-architecture.md`).
2. **Given** a pull request whose description lists requirement IDs that do not exist in
   `specs/`, **When** checks run, **Then** the check fails and names the unknown IDs.
3. **Given** a lane review reported as FAIL, **When** checks run, **Then** the pull request is
   blocked until a PASS is recorded.

---

### User Story 3 - Trace every requirement to its tests (Priority: P1)

One command lists every functional requirement in `specs/` with the tests named after it, the
tasks that implement it and the merged pull requests that cite it, and highlights requirements
that have no test.

**Why this priority**: "Every requirement has a test" is the constitution's promise; this is how
the team checks it before the feature freeze and shows it in the demo.

**Independent Test**: Run the command on a branch where one requirement has no test and confirm
it is listed as untested.

**Acceptance Scenarios**:

1. **Given** the specs and both code repos, **When** the traceability command runs, **Then** each
   requirement shows its tests (by name), tasks and pull requests.
2. **Given** a requirement on the agreed cut list (specs/README.md), **When** the report runs,
   **Then** it is shown as cut, not as untested.
3. **Given** a test named after a requirement ID that does not exist, **When** the report runs,
   **Then** the test is listed as orphaned.

---

### User Story 4 - Show what the factory produced (Priority: P1)

During the demo the team shows a quality and factory dashboard: tests passing by level,
requirements without tests, the latest evaluation scores against their thresholds, the audit
trail of the demo cases and the factory's own numbers.

**Why this priority**: Half of the Day 3 demo is how the software was built, not only what it
does. The numbers must come from records kept since Day 1; they cannot be rebuilt afterwards.

**Independent Test**: Run the dashboard command after the demo journeys and confirm every
section is filled from real results, with no hand-entered values.

**Acceptance Scenarios**:

1. **Given** merged pull requests, **When** the dashboard is built, **Then** it shows per feature:
   pull requests merged, lane review rounds and the rule IDs reviews cited, requirements with
   tests, and time from first commit to merge.
2. **Given** the latest evaluation runs, **When** the dashboard is built, **Then** it shows each
   score from 002 and 004 next to its threshold, with the date and AI provider of the run.
3. **Given** the demo cases, **When** the dashboard is built, **Then** it shows their audit trail
   summary: caseworker actions, overrides, tool calls and AI cost.

---

### User Story 5 - The demo works every time (Priority: P1)

The team can reset the system to the demo's starting point in one command, and can run the demo
on recorded AI responses if the network or the AI provider fails on the day.

**Why this priority**: A 3-minute live demo with a live model and venue Wi-Fi has many ways to
fail; a reliable fallback protects three days of work.

**Independent Test**: Reset, turn the network off, switch to recorded responses, and run every
demo journey.

**Acceptance Scenarios**:

1. **Given** any system state, **When** the demo reset runs, **Then** the data, the named demo
   households and their cases are back at the demo's starting point.
2. **Given** recorded AI responses for the demo journeys, **When** the recorded-responses switch
   is on, **Then** every demo journey completes with no network calls, and every screen that
   shows AI output says it is a recorded response.
3. **Given** the demo script, **When** the team rehearses it, **Then** each step names the user to
   sign in as, the action, the expected result and the target time.

### Edge Cases

- A pull request changes only `specs/` or docs: no lane review is required, but requirement IDs
  still are when a spec changes.
- A pull request spans two lanes: both lane results are required.
- An evaluation has never been run: the dashboard shows "not run", not zero.
- A recorded response is missing for a demo step: the step fails with a clear message instead of
  calling the live model.
- A pull request description is edited after merge: the factory numbers use the description as
  it was at merge time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-009-01**: Each code repo MUST contain agent instructions for Claude Code and Copilot that
  point at the metarepo rule sets mapped to its paths, the shared pull request template, and a
  setup check command that names any missing tool.
- **FR-009-02**: The main branch of each code repo MUST require a pull request, every check from
  FR-000-16 and FR-009-03 passing, and one approving review; direct pushes MUST be refused.
- **FR-009-03**: A pull request check MUST fail unless the description lists (a) the requirement
  IDs covered, each existing in `specs/`, and (b) a PASS result for every lane whose folders the
  pull request changes, with the number of review rounds and the rule IDs cited in any FAIL round.
- **FR-009-04**: A traceability command MUST list, for every functional requirement, its tests
  (matched by the `test_FR_NNN_nn_` prefix in Python and the `FR-NNN-nn:` prefix in TypeScript
  test names, per `project-rules/testing.md`, in both code repos), tasks in `tasks.md` and
  merged pull requests citing it; it MUST flag requirements without tests, orphaned test names,
  and show agreed cuts as cut.
- **FR-009-05**: A single command MUST build the quality and factory dashboard as a static page:
  tests passed by level, requirements without tests, latest evaluation scores against thresholds
  (002, 004), the audit trail summary of the demo cases (caseworker actions, overrides, tool
  calls, AI cost), and the factory numbers in FR-009-06. It replaces the quality report described
  in the original FR-000-15.
- **FR-009-06**: Factory numbers MUST be computed only from git history and pull request records:
  pull requests merged per feature and lane, lane review rounds and rule IDs cited, requirements
  with tests, share of commits marked as AI-assisted, and time from a feature branch's first
  commit to merge.
- **FR-009-07**: The pull request template MUST contain the fields FR-009-03 and FR-009-06 read,
  in a fixed format that the check can parse.
- **FR-009-08**: A demo reset command MUST restore the data set and put the named demo households
  (FR-003-14) and their cases at the demo's starting point.
- **FR-009-09**: The demo profile MUST have a recorded-responses switch: when on, every AI call
  is answered from responses recorded on a live run of the demo journeys, no network call is made,
  and AI output is labelled as recorded.
- **FR-009-10**: A demo script MUST exist in the metarepo listing each step's user, action,
  expected result and target time, matching the journeys in FR-000-19.
- **FR-009-11**: The metarepo MUST have a check that the Copilot files are in sync
  (`scripts/sync-copilot.py --check`) and that requirement IDs in `specs/` are unique.

### Key Entities

- **Pull request record**: repo, feature, requirement IDs, lane results (lane, result, rounds,
  rule IDs cited), AI-assisted flag, merged time.
- **Traceability row**: requirement ID, tests, tasks, pull requests, status (tested, untested,
  cut).
- **Recorded response**: demo step, AI call identity, recorded output, recorded time and provider.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-009-01**: 100% of pull requests merged after Day 1 morning pass the process check.
- **SC-009-02**: At the Day 3 feature freeze, the traceability report shows zero untested
  requirements outside the agreed cut list.
- **SC-009-03**: The dashboard builds in under 2 minutes and contains no hand-entered values.
- **SC-009-04**: All six demo journeys complete on recorded responses with the network off.
- **SC-009-05**: Factory numbers cover 100% of merged pull requests in both code repos.

## Assumptions

- Pull request descriptions are the record of lane reviews; no separate store is kept.
- Factory scripts that read `specs/` live in the metarepo (`scripts/factory/`), because only the
  metarepo can see the specs and both code repos together. This is the one feature allowed to
  write code in the metarepo.
- If time runs short, the dashboard falls back to a Markdown report with the same sections.
