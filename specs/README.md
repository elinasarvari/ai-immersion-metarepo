# Specs: Benefit Case Platform

Feature specs for the 3-day build. Each folder was created with Spec Kit's
`create-new-feature.sh` and holds a `spec.md` (what and why, no technology choices) and a
quality checklist. Plans and tasks are produced by the lane owner with `/speckit-plan` and
`/speckit-tasks` **after** the spec review.

Status: **Draft for team review** (2026-11-09).

## Feature map

| Feature | Lane | Target repo(s) | Depends on | In Day 1 contracts PR? |
|---|---|---|---|---|
| [000 Platform foundations](000-platform-foundations/spec.md) | Platform & UI | benefit-be, benefit-fe | none | Yes |
| [001 Case lifecycle](001-case-lifecycle/spec.md) | Workflows | benefit-be | 000, 002*, 003*, 004* | Yes (states, signals) |
| [002 Document verification](002-document-verification/spec.md) | Agents | benefit-be | 000, 003, 004, 005 | Interface only |
| [003 Eligibility rules and synthetic data](003-eligibility-rules/spec.md) | Knowledge & data | benefit-be | 000 | Yes (rules interface) |
| [004 Policy search and decision explanations](004-policy-search/spec.md) | Knowledge & data, Agents | benefit-be | 000, 003* | Interface only |
| [005 Agent tool access](005-agent-tool-access/spec.md) | Platform & UI | benefit-be | 000, 003, 004 | Yes (tool schemas) |
| [006 Caseworker console and applicant portal](006-caseworker-applicant-portal/spec.md) | Platform & UI | benefit-fe, benefit-be | 000, 001, 003, 004, 007 | Yes (REST API) |
| [007 Redeterminations](007-redeterminations/spec.md) | Workflows | benefit-be | 001, 002, 003, 005 | No |
| [008 Program metrics](008-program-metrics/spec.md) | Knowledge & data, Platform & UI | benefit-be, benefit-fe | 001, 003, 006, 007 | No |
| [009 Delivery factory and demo readiness](009-delivery-factory/spec.md) | Platform & UI | benefit-be, benefit-fe, metarepo `scripts/factory/` | 000; reads every feature's results | Yes (repo setup, PR template) |

\* Built against stubs until the real implementation lands.

## Lanes and the folders they own

Lanes match `project-rules/README.md` and the lane agents in `agents/`. Paths are from the
`benefit-be` repo root, per `project-rules/backend-architecture.md`. A lane edits only its own
folders; changes anywhere else go through the owning lane.

| Lane | Features it leads | benefit-be | benefit-fe |
|---|---|---|---|
| **Workflows** | 001, 007 | `apps/worker/` | none |
| **Agents** | 002, 004 (explanations) | `packages/agents/`; extraction, explanation and agent-success evals in `evals/` | none |
| **Knowledge & data** | 003, 004 (search), 008 (reporting store) | `packages/rag/`, `packages/rules/`, `db/` (baseline migration, `db/seeds/`), `analytics/`, `data/policy/`; retrieval evals | none |
| **Platform & UI** | 000, 005, 006, 008 (metrics page), 009 | `apps/api/`, `packages/mcp_servers/`, `packages/platform/`, `Makefile`, `Procfile`, `.env.example`, CI workflows; metarepo `scripts/factory/` | whole repo |

Shared: `packages/domain/` changes only through a contracts PR reviewed by every lane.
Tests in `tests/` mirror the source tree and belong to the lane that owns the source folder.
Knowledge & data writes the baseline migration (every table, including users) in the contracts PR.

## Rotation

Four lanes, three people. Workflows and Agents form one seat, because activities call agents
through a single shared contract; Knowledge & data and Platform & UI are a seat each. People
rotate seats at each integration checkpoint so everyone works on every side.

| Session | Person 1 | Person 2 | Person 3 |
|---|---|---|---|
| Day 1 morning | Contracts PR together | Contracts PR together | Contracts PR together |
| Day 1 afternoon | Workflows + Agents | Knowledge & data | Platform & UI |
| Day 2 morning | Knowledge & data | Platform & UI | Workflows + Agents |
| Day 2 afternoon | Platform & UI | Workflows + Agents | Knowledge & data |
| Day 3 | Hardening in current seat | Hardening in current seat | Hardening in current seat |

Before each rotation: merge everything, tick completed tasks in `tasks.md`, write `handoff.md`
in each feature folder you touched, and spend 10 minutes walking the next person through it.
The incoming person reviews the outgoing person's last PR.

`handoff.md` template:

```markdown
# Handoff: <feature> (<date>, <session>)
- State: what works now
- In progress: branch, PR, what's half done
- Open issues and decisions needed
- Next task: T0xx from tasks.md
```

## Shared contracts outline (Day 1 contracts PR)

Agreed and merged before the lanes split. This is an outline; the PR holds the real
definitions.

- **Domain models**: User, SystemCredential, Household, HouseholdMember, HouseholdSnapshot,
  CoveragePeriod (with status), Case, CaseEvent, Document, Extraction, Finding,
  VerificationResult, Notice and NoticeDraft (type from FR-001-17), ReviewTask (reason from
  FR-001-19), CaseworkerAction (action from FR-001-19), RuleSet, Determination,
  DecisionExplanation, ToolCallRecord, AuditLogEntry.
- **PostgreSQL** (baseline migration): users, households, household members, household
  snapshots, coverage periods, cases, case events, review tasks, caseworker actions, rule sets, determinations (with
  explanations), `audit_log` (append-only), `outbox` (notices), `policy_passages` (text, citation,
  vector and keyword index).
- **MongoDB** collections: `documents` (upload metadata), `extractions`, `agent_runs` (verification
  and explanation run records with cost), `notice_drafts` (drafts and revisions), `tool_calls`, `eval_overrides` (caseworker overrides
  read by the evaluation command).
- **Reporting store** (008): built from PostgreSQL by dbt into DuckDB; pseudonymous keys only.
- **Case workflow**: states (Submitted, Verifying, Awaiting applicant, Determining, Under
  review, Decided); outcomes (Approved; Denied with reason code: income over limit, other rule
  not met, missing information; redeterminations: renewed automatically, renewed after
  response, ended by caseworker decision); signals (caseworker action, applicant response,
  advance clock in demo profile only); timers (response deadline, review reminder, review
  escalation, redetermination start). Redeterminations use the same states with no 45-day
  deadline, in the same workflow type (`CaseWorkflow` with a case type), started by the daily
  schedule or on demand through the API with the same workflow ID (FR-007-15). Every case keeps
  a case clock (FR-001-13). Review reasons and the actions each allows are the table in
  FR-001-19; notice types are the table in FR-001-17.
- **Interfaces between lanes**:
  - `verify_documents(case_id) -> VerificationResult` (Agents provides; Workflows uses)
  - `evaluate(household, as_of_date) -> Determination` (Knowledge & data provides; called only
    by worker activities. Platform & UI reads stored determinations.)
  - `search_policy(query) -> list[PolicyPassage]` (Knowledge & data provides; Agents uses)
  - `explain_determination(determination, audience) -> DecisionExplanation` (Agents provides;
    called by worker activities after each determination. Platform & UI reads stored explanations.)
  - `draft_request(case_id, items) -> NoticeDraft` (Agents provides; used for requests
    for information and redetermination forms)
- **Agent tools** (005): input and output schema for each of the 11 tools.
- **REST API** (006): endpoint list and OpenAPI document; the UI builds against stub
  responses until each endpoint is real. The OpenAPI file is committed in benefit-be (FR-000-26).
- **Repo setup and PR template** (009): agent instructions, PR template fields, required checks
  and branch protection in both code repos, in place before the first feature branch.

## Project values

Fixed values for this training build. They are modelled on federal Medicaid rules but are not
checked against current regulation, and every spec uses them.

| Value | Project value | Used in |
|---|---|---|
| Decision deadline | 45 days from receipt | 001, 008 |
| Response window for a request for information | 15 days | 001, 002 |
| Redetermination start | 60 days before coverage ends | 007 |
| Redetermination form response window | 30 days | 007 |
| Coverage period | 12 months | 007 |
| Income limit | 138% of the poverty guideline | 003 |
| Poverty guideline, previous year | $15,000 + $5,000 per additional person (annual) | 003 |
| Poverty guideline, current year | $15,500 + $5,200 per additional person (annual) | 003 |
| Policy manual | Training edition written by the team, 25–40 sections | 004 |
| Day counting | Calendar days for every window and reminder | all |
| Review reminder / escalation | 2 days / 4 days (escalated tasks flagged for supervisors) | 001, 006 |
| Demo time scale | 1 day = 1 minute, plus a supervisor "advance clock" action | 001, 007 |
| Seeded years | 2 (previous and current program years) | 003 |
| Program years | Calendar years: previous 2025, current 2026 | 003 |
| Time zone | America/Chicago for all dates and day counts | all |
| Coverage start | First day of the month the application was received; renewals start the day after the previous period ends | 001, 007 |
| Monthly income from a pay stub | Weekly × 52 ÷ 12, bi-weekly × 26 ÷ 12, semi-monthly × 2, monthly × 1, to the cent; most recent stub per job | 002, 003 |
| Pay stub recency | Dated within 45 days before receipt (or redetermination start) | 002 |
| Mismatch threshold | More than 10% between declared, documented or source income | 002, 007 |
| Requests for information | At most one drafted automatically per case; one 15-day extension per request | 001 |
| Uploads | PDF, PNG or JPEG, up to 10 MB each, up to 10 files | 006 |
| Session length | 8 hours | 000 |
| Metrics refresh | Every hour; every 5 minutes in the demo profile; on demand | 008 |

## Cut first if behind

If the team is behind at a checkpoint, cut in this order. Every cut keeps the demo story intact.

1. P3 stories: deadline visibility (001 US6) and upcoming redeterminations (007 US4,
   FR-006-16).
2. Program metrics down to four (008 assumptions).
3. Review escalation flag at 4 days (keep the 2-day reminder).
4. Automated accessibility check (keep accessible markup; check by hand).
5. Policy manual down to 15 sections and 20 evaluation questions.
6. Poor-quality scanned pay stubs.
7. Factory dashboard down to a Markdown report with the same sections (009).

Never cut: the repo setup and pull request check (009 US1–US2) and the recorded-responses demo
switch (FR-009-09). They protect everything else.

## Test strategy

Each lane writes unit, workflow and integration tests for its own features. Platform & UI owns
CI, the test harnesses and the end-to-end suite; each lane adds the end-to-end journey for its
feature.

| Level | What it checks | Tool | Runs |
|---|---|---|---|
| Static | Lint, formatting, strict types, dependency and secrets scans | ruff, mypy, tsc, pip-audit, npm audit, gitleaks | Every PR |
| Unit | One behaviour per test, named after its `FR-` | pytest, Vitest + Testing Library | Every PR |
| Workflow | State changes, timers, signals, restart and replay | Temporal test environment | Every PR |
| Contract | API matches its contract; tool schemas; generated frontend client | OpenAPI diff, JSON Schema | Every PR |
| Integration | API, workers and tools against local databases; access rules | pytest with local PostgreSQL, MongoDB, Temporal | Every PR |
| End-to-end | The six demo journeys through real screens (AI faked) | Playwright | Every PR |
| Accessibility | WCAG 2.1 AA on every screen | axe with Playwright | Every PR |
| LLM evaluation | Extraction, mismatches, citations, retrieval, explanations | `make eval` (live model) | On demand, before the demo |

No test level in CI calls a live AI model. Load and performance testing are out of scope.

## Conventions

- Requirement IDs are feature-scoped: `FR-<feature>-<nn>`, success criteria `SC-<feature>-<nn>`.
- Tests are named after the requirement they prove: `test_FR_001_06_no_automatic_denial`.
- `plan.md` names its target repo(s) and uses the backend layout in `project-rules/`.
- Branch `feature/<NNN-feature>` in every repo the feature touches; one PR per repo.

## Reviewing a spec

Each spec is reviewed by the lane that **uses** what it provides (see "Depends on"). Check:

- Can you build against it without asking the owner anything?
- Is every requirement testable, with a number or named state where it matters?
- Does "Out of scope" stop it drifting into your lane?

## Open items before planning

- [x] 004: policy manual source. Decided: a training-edition manual written by the team (see 004
      Assumptions).
- [x] 001, 003 and 007: program values. Decided: fixed project values (see "Project values").
- [x] Seed data and evaluation sets. Decided: `benefit-be/db/seeds/` and `benefit-be/evals/`, with the
      manual in `data/policy/` (BA-10 to BA-12 in `project-rules/backend-architecture.md`).
- [x] `project-rules/` conflicts. Fixed: `frontend-react.md` now states a Vite single-page app
      with no Server Components, and `backend-architecture.md` assigns ownership by lane.

## Spec review round 2 (2026-11-09): defaults to confirm in PR review

A completeness review found gaps that would have changed the schema, contracts or workflow
signals mid-build. Each was closed with the default below; overrule any of them in PR review,
before the contracts PR.

- [ ] Income used by the rules: verified pay stub income, summed per member and job; zero income
      on attestation (FR-003-17, FR-003-18, FR-002-15).
- [ ] Pay stubs also yield employee name and pay frequency; a stub for no household member is a
      finding (FR-002-01, FR-002-14).
- [ ] Verification calls the identity and income sources; that check sets "identity verified"
      (FR-002-13, FR-005-12).
- [ ] The application form fields (FR-006-07); attested facts come from it for new households
      (FR-003-16).
- [ ] Evaluation runs on a household snapshot per case (FR-003-19).
- [ ] Any failed rule means Ineligible; income over limit wins as the reason code (FR-003-20,
      FR-001-16).
- [ ] Program years 2025 and 2026; as-of date rules (FR-003-21); time zone (FR-000-27).
- [ ] Seeded history is loaded directly, not through workflows (FR-003-22).
- [ ] Case clock for the demo profile (FR-001-13).
- [ ] Review reasons and actions (FR-001-19); notice types (FR-001-17); one automatic request for
      information (FR-001-21); overrides leave the determination unchanged (FR-001-20).
- [ ] Coverage start and status (FR-001-22, FR-007-14); duplicate applications (FR-001-23).
- [ ] What "missing or out of date" means at renewal (FR-007-13); one workflow type for
      applications and redeterminations, started by the schedule or on demand (FR-007-15, TW-6).
- [ ] System credential for agent tools (FR-000-22, FR-005-10); audit log contents (FR-000-23).
- [ ] CI on hosted runners with a fake embedder; end-to-end suite in benefit-fe; OpenAPI file
      committed in benefit-be (FR-000-24 to FR-000-26).
- [ ] Synthetic marker per store, not per record (FR-000-14).
- [ ] Metric periods, AI override rate definition, refresh interval (FR-008-01, FR-008-08).
- [ ] New screens and actions the demo needs: AI activity, notices list, upcoming
      redeterminations, start redetermination (FR-006-14 to FR-006-17).
- [ ] New feature 009: repo setup, pull request check, traceability, factory dashboard,
      recorded-responses demo switch, demo script.
