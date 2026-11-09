# Specs: Benefit Case Platform

Feature specs for the 3-day build. Each folder was created with Spec Kit's
`create-new-feature.sh` and holds a `spec.md` (what and why, no technology choices) and a
quality checklist. Plans and tasks are produced by the lane owner with `/speckit-plan` and
`/speckit-tasks` **after** the spec review.

Status: **Draft for team review** (2026-11-09).

## Feature map

| Feature | Lane | Target repo(s) | Depends on | In Day 1 contracts PR? |
|---|---|---|---|---|
| [000 Platform foundations](000-platform-foundations/spec.md) | C | benefit-be, benefit-fe | none | Yes |
| [001 Case lifecycle](001-case-lifecycle/spec.md) | A | benefit-be | 000, 002*, 003*, 004* | Yes (states, signals) |
| [002 Document verification](002-document-verification/spec.md) | B | benefit-be | 000, 003, 004, 005 | Interface only |
| [003 Eligibility rules and synthetic data](003-eligibility-rules/spec.md) | A | benefit-be | 000 | Yes (rules interface) |
| [004 Policy search and decision explanations](004-policy-search/spec.md) | B | benefit-be | 000, 003* | Interface only |
| [005 Agent tool access](005-agent-tool-access/spec.md) | B | benefit-be | 000, 003, 004 | Yes (tool schemas) |
| [006 Caseworker console and applicant portal](006-caseworker-applicant-portal/spec.md) | C | benefit-fe, benefit-be | 000, 001, 003, 004, 007 | Yes (REST API) |
| [007 Redeterminations](007-redeterminations/spec.md) | A | benefit-be | 001, 002, 003, 005 | No |
| [008 Program metrics](008-program-metrics/spec.md) | C | benefit-be, benefit-fe | 001, 003, 006, 007 | No |

\* Built against stubs until the real implementation lands.

## Lanes and the folders they own

Paths follow `project-rules/backend-architecture.md`. A lane edits only its own folders; changes
anywhere else go through the owning lane.

| Lane | Features | benefit-be | benefit-fe |
|---|---|---|---|
| **A: Workflows and decisions** | 001, 003, 007 | `api/apps/worker/`, `api/packages/rules/`, `api/db/migrations/`, `api/seed/` (except `policy_manual/`; writes `seed/generated/`) | none |
| **B: AI and knowledge** | 002, 004, 005 | `api/packages/agents/`, `api/packages/rag/`, `api/packages/mcp_servers/`, `api/evals/`, `api/seed/policy_manual/` | none |
| **C: Platform and experience** | 000, 006, 008 | `api/apps/api/`, `api/analytics/`, `api/packages/platform/`, `Makefile`, `Procfile`, `.env.example` | whole repo |

Shared: `api/packages/domain/` changes only through a contracts PR reviewed by all three lanes.
Tests in `api/tests/` mirror the source tree and belong to the lane that owns the source folder.
Lane A writes the baseline migration (every table, including users) in the contracts PR.

## Rotation

Lanes stay fixed; people rotate at each integration checkpoint so everyone works on every side.

| Session | Person 1 | Person 2 | Person 3 |
|---|---|---|---|
| Day 1 morning | Contracts PR together | Contracts PR together | Contracts PR together |
| Day 1 afternoon | Lane A | Lane B | Lane C |
| Day 2 morning | Lane B | Lane C | Lane A |
| Day 2 afternoon | Lane C | Lane A | Lane B |
| Day 3 | Hardening in current lane | Hardening in current lane | Hardening in current lane |

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

- **Domain models**: User, Household, HouseholdMember, CoveragePeriod, Case, CaseEvent,
  Document, Extraction, Finding, VerificationResult, NoticeDraft, ReviewTask,
  CaseworkerAction, RuleSet, Determination, ToolCallRecord.
- **PostgreSQL** (baseline migration): users, households, household members, coverage periods,
  cases, case events, review tasks, caseworker actions, rule sets, determinations (with
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
  deadline.
- **Interfaces between lanes**:
  - `verify_documents(case_id) -> VerificationResult` (B provides, A uses)
  - `evaluate(household, as_of_date) -> Determination` (A provides; called only by worker
    activities. C reads stored determinations.)
  - `search_policy(query, as_of_date) -> list[PolicyPassage]` (B provides, B uses)
  - `explain_determination(determination, audience) -> DecisionExplanation` (B provides;
    called by worker activities after each determination. C reads stored explanations.)
  - `draft_request(case_id, items) -> NoticeDraft` (B provides; used for requests for
    information and redetermination forms)
- **Agent tools** (005): input and output schema for each of the 11 tools.
- **REST API** (006): endpoint list and OpenAPI document; the UI builds against stub
  responses until each endpoint is real.

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

## Cut first if behind

If the team is behind at a checkpoint, cut in this order. Every cut keeps the demo story intact.

1. P3 stories: deadline visibility (001 US6) and upcoming redeterminations (007 US4).
2. Program metrics down to four (008 assumptions).
3. Review escalation flag at 4 days (keep the 2-day reminder).
4. Automated accessibility check (keep accessible markup; check by hand).
5. Policy manual down to 15 sections and 20 evaluation questions.
6. Poor-quality scanned pay stubs.

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
- [x] Seed data and evaluation sets. Decided: `benefit-be/api/seed/` and `benefit-be/api/evals/`,
      added to `project-rules/backend-architecture.md`.
- [x] `project-rules/` conflicts. Fixed: `frontend-react.md` now states a Vite single-page app
      with no Server Components, and `backend-architecture.md` assigns ownership by lane.
