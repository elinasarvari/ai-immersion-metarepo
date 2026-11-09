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
| [001 Case lifecycle](001-case-lifecycle/spec.md) | A | benefit-be | 000, 002*, 003* | Yes (states, signals) |
| [002 Document verification](002-document-verification/spec.md) | B | benefit-be | 000, 004, 005 | Interface only |
| [003 Eligibility rules and synthetic data](003-eligibility-rules/spec.md) | A | benefit-be | 000 | Yes (rules interface) |
| [004 Policy search and decision explanations](004-policy-search/spec.md) | B | benefit-be | 000, 003* | Interface only |
| [005 Agent tool access](005-agent-tool-access/spec.md) | B | benefit-be | 000, 003, 004 | Yes (tool schemas) |
| [006 Caseworker console and applicant portal](006-caseworker-applicant-portal/spec.md) | C | benefit-fe, benefit-be | 000, 001, 003, 007 | Yes (REST API) |
| [007 Redeterminations](007-redeterminations/spec.md) | A | benefit-be | 001, 002, 003, 005 | No |
| [008 Program metrics](008-program-metrics/spec.md) | C | benefit-be, benefit-fe | 001, 003, 006, 007 | No |

\* Built against stubs until the real implementation lands.

## Lanes and the folders they own

Paths follow `project-rules/backend-architecture.md`. A lane edits only its own folders; changes
anywhere else go through the owning lane.

| Lane | Features | benefit-be | benefit-fe |
|---|---|---|---|
| **A: Workflows and decisions** | 001, 003, 007 | `api/apps/worker/`, `api/packages/rules/`, `api/db/migrations/`, synthetic data generator | none |
| **B: AI and knowledge** | 002, 004, 005 | `api/packages/agents/`, `api/packages/rag/`, `api/packages/mcp_servers/` | none |
| **C: Platform and experience** | 000, 006, 008 | `api/apps/api/`, `api/analytics/`, shared config and logging | whole repo |

Shared: `api/packages/domain/` changes only through a contracts PR reviewed by all three lanes.

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
  and explanation run records with cost), `notice_drafts` (drafts and revisions), `tool_calls`.
- **Reporting store** (008): built from PostgreSQL by dbt into DuckDB; pseudonymous keys only.
- **Case workflow**: states (Submitted, Verifying, Awaiting applicant, Determining, Under
  review, Decided); signals (caseworker action, applicant response); timers (response
  deadline, review reminder, review reassignment, redetermination start).
- **Interfaces between lanes**:
  - `verify_documents(case_id) -> VerificationResult` (B provides, A uses)
  - `evaluate(household, as_of_date) -> Determination` (A provides, A and C use)
  - `search_policy(query, as_of_date) -> list[PolicyPassage]` (B provides, B uses)
  - `explain_determination(determination, audience) -> DecisionExplanation` (B provides, A and C use)
- **Agent tools** (005): input and output schema for each of the 11 tools.
- **REST API** (006): endpoint list and OpenAPI document; the UI builds against stub
  responses until each endpoint is real.

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

- [ ] 004: confirm the Illinois DHS policy manual URL and whether its terms of use allow a
      local copy (the one `[NEEDS CLARIFICATION]` marker).
- [ ] 001 and 007: confirm the 15-day and 30-day response windows and the 12-month renewal
      period against current federal Medicaid rules (42 CFR Part 435).
- [ ] 003: confirm the 138% income limit for Illinois adults and copy the federal poverty
      guidelines for both program years into configuration, with the source recorded.
- [ ] Decide where the synthetic data generator and evaluation sets live in benefit-be, and add
      them to `project-rules/backend-architecture.md`.
- [ ] Fix two `project-rules/` conflicts: `frontend-react.md` asks for Server Components (not
      available in a Vite single-page app) and `backend-architecture.md` says Workflows and
      Agents have separate owners (conflicts with rotation).
