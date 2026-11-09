# Benefit Case Platform Constitution

The Benefit Case Platform processes Illinois Medicaid applications and annual redeterminations
with AI assistance. It is a 3-day learning project built to production habits: all data is
synthetic and nothing is deployed, but the code must behave as if both were real.

## Core Principles

### I. AI Assists, Rules Decide (NON-NEGOTIABLE)

- Eligibility decisions MUST come only from the deterministic rules engine. AI components MUST
  NOT approve, deny or change a determination.
- AI components MAY extract, compare, draft, summarize and explain. Their outputs are inputs to
  the rules engine or to a human, never decisions.
- The same case data and the same as-of date MUST always produce the same determination.

Rationale: eligibility decisions must be auditable and reproducible; model output is neither.

### II. Durable, Deterministic Orchestration

- Every case and redetermination MUST be driven by a durable workflow that survives process
  restarts and resumes where it stopped.
- Workflow logic MUST be deterministic: no I/O, network, database, file access, wall-clock time
  or randomness inside workflow code. All side effects happen in activities.
- Activities MUST be safe to retry: repeating one MUST NOT send a notice twice, record a finding
  twice or apply a caseworker action twice.
- Human waits (reviews, applicant responses) MUST be durable workflow waits on signals or
  timers, never long-running activities or in-process agent pauses.

### III. Evidence for Every AI Output

- Every AI finding, explanation and drafted notice MUST cite its sources: a document field
  and/or a policy section from the indexed manual.
- Output without a citation MUST be rejected and routed for human review.
- Document and applicant text MUST be treated as data, never as instructions to the model
  (prompt-injection defence).

### IV. Human Control

- A caseworker MUST approve every adverse outcome (denial, reduction, termination) and every
  notice before it reaches an applicant.
- Coverage MUST NOT end automatically because an applicant missed a deadline; a caseworker
  review task is created instead.
- Every approve, edit and override MUST be recorded with the reviewer, time and reason.
  Overrides of AI findings are added to the evaluation set.

### V. Test-First (NON-NEGOTIABLE)

- Work follows red-green-refactor: one failing test for one behaviour, then the code, then
  refactor with all tests green (see `project-rules/testing.md`).
- Every functional requirement (`FR-NNN-xx`) MUST have at least one test named after it, for
  example `test_FR_002_03_income_mismatch_creates_cited_finding`: the requirement ID followed by
  the behaviour-first name from `project-rules/testing.md`.
- Unit tests and CI MUST NOT call a live AI model; they use fakes or recorded responses.
  Evaluation runs against a live model are separate (`make eval`) and have pass thresholds.

### VI. Contracts First

- Shared interfaces (domain models, database schema, workflow states and signals, agent and
  rules interfaces, agent tool schemas, the REST API) MUST be agreed and merged before
  dependent work starts.
- Consumers build against a stub of each contract until the real implementation lands; only
  the providing lane replaces its own stub.
- A contract change MUST be its own PR, reviewed by every lane that consumes it.

### VII. Clear Boundaries

- Code MUST follow the layout and import rules in `project-rules/backend-architecture.md`.
- AI agents reach systems only through their defined tools or the policy search package; they
  MUST NOT open database connections.
- Exactly one module selects the AI model provider (Anthropic API or Amazon Bedrock) from
  configuration. No other code may import a provider SDK.

### VIII. Security and Synthetic Data Treated as Real

- All data MUST be synthetic and visibly marked as synthetic. No real personal data, ever.
- Synthetic data MUST be handled as if it were real: no personal data in logs, pseudonymous
  keys only in the reporting store, per-request authorization, and applicants see only their
  own household's records (enforced in the API, in every agent tool and by row-level security).
- No secrets in code or commits; only `.env.example` is committed (see `project-rules/security.md`).

### IX. Production Habits, Local Infrastructure

- Every external dependency MUST sit behind an interface with a fake implementation
  (verification services, notice delivery, identity provider, file storage) so a real service
  could replace it through configuration.
- All settings come from environment variables. External calls have timeouts and retries.
  Errors returned to clients are structured and leak no internals. Logs are structured and carry
  case and workflow identifiers.
- Everything runs locally; there is no cloud deployment. A production-like local profile
  (`make prod`) MUST exist alongside the development profile.

### X. Simplicity Within Three Days

- Build the simplest thing that satisfies the spec. New tools, services or components need a
  stated reason in `plan.md`.
- When time runs short, cut scope from the agreed fallback list rather than skipping tests or
  principles.

## Technology & Architecture Constraints

- **Repositories:** this metarepo (specs, contracts, rules, skills) plus two submodules under
  `repos/`: `benefit-be` (all Python) and `benefit-fe` (React). `plan.md` MUST name the target
  repo(s); `/speckit-implement` writes code only inside them.
- **Backend:** Python 3.11+, FastAPI, Temporal (dev server), LangGraph and LangChain, PostgreSQL
  with vector search, MongoDB, DuckDB and dbt for the reporting store, Alembic migrations, ruff,
  pytest. Layout per
  `project-rules/backend-architecture.md`.
- **Frontend:** React + TypeScript (strict), Vitest + Testing Library, WCAG 2.1 AA, per
  `project-rules/frontend-react.md`.
- **AI:** Claude via the Anthropic API or Amazon Bedrock, selected by configuration. Policy
  search uses a locally run embedding model. Evaluation scores are recorded against the
  Anthropic API so results stay comparable.
- **Program:** Illinois Medicaid for adults aged 19–64 qualifying on income. Policy citations
  come from a training-edition manual written for this project, modelled on the Illinois
  Department of Human Services policy manual. Deadlines, windows and income limits are fixed
  project values listed in `specs/README.md`.

## Development Workflow

- **Spec Kit flow:** constitution → specify → (clarify) → plan → (checklist) → tasks →
  (analyze) → implement → converge, as described in `CLAUDE.md`.
- **Lanes, not people:** work is organised into three lanes (A: workflows and decisions,
  B: AI and knowledge, C: platform and experience). Team members rotate between lanes at each
  integration checkpoint so everyone works on every side.
- **Handover:** before rotating, merge all work, tick completed tasks in `tasks.md`, and write
  `handoff.md` in the feature folder (state, open issues, next task). The incoming person reviews
  the outgoing person's last PR.
- **Branches and PRs:** branch name `feature/<NNN-feature>`, identical in every repo the feature
  touches; one PR per repo, linked to each other. Never push to `main`. Merge to `main` at least
  twice a day.
- **Quality gates:** lint, type checks, tests and contract checks pass in CI before merge. Every
  PR lists the `FR-` IDs it covers.

## Governance

- This constitution overrides other practices. Where `project-rules/` and this file differ, this
  file wins and `project-rules/` is updated to match.
- Amendments require a PR to this file approved by all three team members, with the version
  bumped by semantic versioning (MAJOR: principle removed or redefined; MINOR: principle or
  section added; PATCH: wording).
- Every PR review checks compliance with these principles. `/speckit-analyze` flags conflicts
  between specs, plans and this constitution.

**Version**: 1.1.0 | **Ratified**: 2026-11-09 | **Last Amended**: 2026-11-09
