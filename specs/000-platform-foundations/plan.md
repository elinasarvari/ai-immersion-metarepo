# Implementation Plan: Platform Foundations

**Branch**: `feature/000-platform-foundations` (benefit-be and benefit-fe) | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/000-platform-foundations/spec.md`

**Lane**: Platform & UI (lead). Workflows, Agents, and Knowledge & data each supply their part (below).

**Target repos**: `repos/benefit-be`, `repos/benefit-fe`

**Artifacts**: [research.md](research.md) · [data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

## Summary

This feature builds the base that every other feature runs on:

- **One-command runs**: `make dev` and `make prod` start every native process through honcho. `make reset` clears all data and reseeds while the system is running.
- **Settings**: one fail-fast `Settings` class. `.env.example` is committed.
- **Sign-in**: seeded demo accounts with three roles, argon2id password hashes, and a JWT kept in an HttpOnly same-origin cookie, behind an `IdentityProvider` interface.
- **Agent tool credential**: a case-scoped system credential that the worker mints for agent tools.
- **Errors**: one structured error envelope with a reference ID.
- **Health**: health and readiness checks on every component.
- **Logs**: structlog JSON with personal data masked.
- **Outbound calls**: timeouts and bounded retries on every call.
- **AI provider**: Anthropic API or Bedrock, chosen by configuration in one factory.
- **Tracing**: Arize Phoenix with masked spans.
- **Audit**: an append-only audit log.
- **Synthetic markers**: one per data store, plus a visible SYNTHETIC label on every generated document through one shared stamping helper (R24).
- **CI**: a pipeline in both repos with static, unit, workflow, contract, integration and end-to-end jobs. The end-to-end suite lives in `benefit-fe`, and its six journeys start out as pending.

The scaffolds are first brought into line with the rules: `app/` → `apps/api/`, uv, pnpm, ESLint and strict TypeScript (research R1).

## Technical Context

**Language/Version**:
- Backend: Python 3.12 (R2)
- Frontend: TypeScript 5.9.3 on Node 24 LTS (R3)

**Primary Dependencies**:
- Backend:
  - API and settings: FastAPI 0.16x, Pydantic v2, pydantic-settings 2.16
  - Auth: PyJWT 2.15, argon2-cffi 25.1
  - Logging and retries: structlog 26.1, httpx 0.28
  - Workflows: temporalio 1.35
  - Data: PyMongo 4.19 (async API), numpy for in-app policy search (004)
  - Models: langchain-anthropic 1.7, langchain-aws 1.9
  - Tracing: openinference-instrumentation-langchain, opentelemetry-sdk
  - Run and checks: honcho 2.0, pip-audit, mypy 2.4, ruff 0.17
  - Document marking: pypdf 7.0, reportlab 5.1, Pillow 13.0 (R24)
- Frontend:
  - App: React 19, Vite 8, react-router 8, TanStack Query 5, Tailwind 4, shadcn/ui
  - API client: openapi-typescript 7.13, openapi-fetch
  - Tests: Vitest 5, Testing Library, @playwright/test 1.65, @axe-core/playwright
  - Lint: ESLint 10, typescript-eslint 8, Prettier 3

All versions are pinned exactly, with `uv.lock` and `pnpm-lock.yaml` committed (PR-4).

**Storage**:
- MongoDB 8.0 (single-node replica set `rs0`, authentication on), the only operational database (R27, draft constitution 2.0.0): `users`, `households` (stub), `audit_log`, `_meta` (the synthetic marker), `_migrations`, and the other bootstrapped collections
- DuckDB, via dbt-duckdb: the marker model, built from the Mongo export
- Temporal dev server: SQLite file in `.data/`
- Phoenix: SQLite in `.data/phoenix`

**Testing**:
- Backend:
  - pytest, with markers `unit`, `workflow`, `contract`, `integration`, `api`, `live_llm`
  - Temporal `WorkflowEnvironment` for workflow tests
  - pytest-playwright `APIRequestContext` for API tests
  - hypothesis for property tests
- Frontend:
  - Vitest with Testing Library
  - Playwright with axe

**Target Platform**:
- Local: native macOS on Apple silicon. `mongod` started by `make mongo-up`, the other processes by honcho; no Docker (PR-5).
- CI: GitHub-hosted `ubuntu-24.04` runners, with MongoDB 8.0 installed from MongoDB's apt repository and started by the same `make mongo-up` (FR-000-24).

**Project Type**: A web service (FastAPI API, Temporal worker, MCP servers in 005) plus a single-page web app. Two repos.

**Performance Goals**:
- A full CI run finishes in under 15 minutes (SC-000-08). R25 has the budget and an `@smoke` fallback.
- Readiness probes time out at 2 s.
- Going from a fresh clone to a healthy system takes under 30 minutes (SC-000-01).
- Load testing is out of scope.

**Constraints**:
- No personal data in logs or traces.
- No live model calls in CI or in any automated test level except `make smoke-ai`.
- No secrets committed.
- Every date uses America/Chicago.
- Sessions last 8 h by default.
- Every outbound call has a timeout and a bounded retry.

**Scale/Scope**:
- 3 developers
- 4 seeded accounts
- 5 local processes, plus 4 MCP servers from 005
- 2 repos with 6 CI jobs each

All `NEEDS CLARIFICATION` items were settled in [research.md](research.md); see "Clarifications resolved" there.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. AI assists, rules decide | No eligibility logic in 000. The model factory only builds clients. | ✅ Pass |
| II. Durable, deterministic orchestration | Credential minting and settings reads happen only in activities and `main.py`. The workflow `calendar.py` uses only `workflow.now()`. There are activity timeout and retry presets. | ✅ Pass |
| III. Evidence for every AI output | Not affected in 000. The smoke test checks cited structured output. | ✅ N/A |
| IV. Human control | Not affected. The audit log records caseworker actions for later features. | ✅ N/A |
| V. Test-first | Every FR-000-xx has a named test (table under "Test plan"). Red-green order is enforced through `tasks.md`. No live model in tests or CI. Every required test level is in CI. | ✅ Pass |
| VI. Contracts first | The `packages/domain` models, baseline tables, OpenAPI document and `tool_credential` signature change go in the Day 1 contracts PR (R23). | ✅ Pass |
| VII. Clear boundaries | The BA layout is restored (R1). The provider SDKs are imported only in `packages/agents/llm/factory.py`, enforced with ruff TID251. `temporalio` stays out of `packages/*`. | ✅ Pass |
| VIII. Security and synthetic data | argon2id, HttpOnly cookie, per-route role checks, repository-layer household scoping (R16), masking of logs and traces, a marker per store, gitleaks, only `.env.example` committed. | ✅ Pass |
| IX. Production habits, local infrastructure | `IdentityProvider` interface with a local fake. Settings come only from the environment. Timeouts and retries. Structured errors and logs. `make dev` and `make prod` live in benefit-be. | ✅ Pass |
| X. Simplicity | Every new tool has a stated reason (table below). Rejected options are listed in research.md: Ed25519, a revocation table, a separate linter, Langfuse and oasdiff. | ✅ Pass |
| Tech constraints | Repos are named. Python 3.12 and a strict React + TypeScript frontend. Commands live in benefit-be. | ✅ Pass |

### Draft constitution amendment: MongoDB only (R27)

The team chose to drop PostgreSQL. `.specify/memory/constitution.md` now carries a **DRAFT AMENDMENT v2.0.0** (principles V and VIII, and the Technology & Architecture Constraints), and the rules in `project-rules/` and `specs/README.md` are updated to match. Governance says an amendment needs a PR approved by all three team members. **This plan is written against the draft.** If the amendment is not approved, the database tasks revert to the version 1.4.1 design described in research R13–R16 as they were before R27. Everything else in the plan is unaffected.

### New tools and services (constitution X: stated reason)

| Tool | Why | Named by rule? |
|---|---|---|
| honcho + Procfiles | Runs every process with one command (FR-000-01) | PL-12 |
| Arize Phoenix (`uvx`, pinned) | Local tracing service (FR-000-28). Runs natively with no Docker. | AG-15, BA |
| PyJWT | Session and system-credential tokens | PL-5 |
| argon2-cffi | Password hashing (FR-000-21) | security.md |
| structlog | Structured logs (FR-000-10) | PL-11 |
| pre-commit + gitleaks | Secrets scan (FR-000-16, SC-000-03) | PL-14 |
| react-router | SPA routing with role guards (FE-6) | — (smallest standard choice, R3) |
| openapi-fetch | Typed fetch over the `openapi-typescript` output (FE-3) | — (made for openapi-typescript) |
| pypdf, reportlab, Pillow | Visible SYNTHETIC label on generated PDFs and images (FR-000-14). 003 already needs reportlab and Pillow to generate pay stubs. | — (R24) |

**Post-design re-check (after Phase 1)**: ✅ All gates still pass. The design adds no new top-level folders beyond BA-1. `scripts/` and `openapi/` are Platform-owned setup folders; PL-* already covers `scripts/`, and `openapi/` holds the FR-000-26 contract file. Note for the PR: add `openapi/` to the BA-1 layout tree in `project-rules/backend-architecture.md`.

## Project Structure

### Documentation (this feature)

```text
specs/000-platform-foundations/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0: decisions R1–R27
├── data-model.md        # Phase 1: entities, tables, domain models
├── quickstart.md        # Phase 1: validation scenarios
├── contracts/
│   ├── rest-api.openapi.yaml   # /api/v1 auth, health, ready; error envelope
│   ├── settings.md             # every .env setting, validation rules
│   ├── logging.md              # log fields, request-id propagation, masking
│   └── commands-and-ci.md      # make targets, processes/ports, CI jobs, pending journeys
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, not created here)
```

### Source code: benefit-be

```text
benefit-be/
├── apps/
│   ├── api/                              # Platform & UI (was app/; git mv)
│   │   ├── main.py                       # create_app(settings) factory
│   │   ├── errors.py                     # exception handlers → ErrorEnvelope
│   │   ├── identity_local.py             # local IdentityProvider (user repository lookup)
│   │   ├── temporal_client.py            # client + x-request-id interceptor
│   │   ├── middleware/request_context.py # X-Request-ID, log binding, access log
│   │   ├── dependencies/{auth.py,db.py}  # current_principal, require_roles, Scope from the Principal
│   │   ├── routers/{auth.py,health.py}
│   │   ├── services/{auth_service.py,readiness.py}
│   │   ├── repositories/users.py
│   │   └── schemas/{auth.py,health.py}
│   └── worker/                           # Workflows
│       ├── main.py                       # settings → logging → health server → Temporal connect (backoff) → Worker
│       ├── health.py                     # /health, /ready on WORKER_HEALTH_PORT
│       ├── interceptors.py               # bind workflow_id/case_id/request_id for activities
│       ├── policies.py                   # DEFAULT / AGENT_STEP activity presets
│       ├── workflows/{calendar.py,smoke.py}
│       └── activities/agent_step.py      # mints system credential per attempt
├── packages/
│   ├── domain/                           # Shared (contracts PR): auth, audit, errors, health, dataset, agent_run
│   ├── platform/                         # Platform & UI
│   │   ├── settings.py  clock.py  logging.py  errors.py  resilience.py  audit.py  health.py
│   │   ├── synthetic.py                  # stamp_pdf / stamp_image / stamp_text / is_marked (FR-000-14)
│   │   └── auth/{passwords.py,tokens.py,identity.py,roles.py}
│   ├── agents/                           # Agents
│   │   ├── llm/{factory.py,fake.py,pricing.py}
│   │   ├── tracing.py                    # OpenInference + MaskingSpanExporter
│   │   └── prompts/                      # empty, versioned (AG-13)
│   └── rag/{embeddings.py,rerank.py,factory.py}  # Knowledge & data: real + Fake embedder/reranker
├── db/                                   # Knowledge & data
│   ├── mongo/provision.py                # replica set, users benefit_owner/benefit_app, auditAppend role
│   ├── migrate.py                        # runs versioned migrations, records them in _migrations
│   ├── migrations/versions/0001_baseline.py  # collections, validators, indexes, _meta
│   └── seeds/{generate.py,users.py,reset.py}   # generated/ is git-ignored
├── analytics/                            # Knowledge & data: dbt-duckdb, meta.dataset_metadata only
├── openapi/openapi.json                  # generated + committed (FR-000-26)
├── scripts/{export_openapi.py,check_health.py,ci/resolve-sibling-ref.sh,ci/wait-ready.sh}
├── tests/                                # mirrors source; conftest sets APP_ENV=test, LLM_MODE=fake
│   ├── apps/api/…  apps/worker/…(+histories/smoke_v1.json)
│   ├── packages/platform/…  packages/agents/…  packages/rag/…
│   ├── db/…  contract/…  integration/…  api/…
├── .github/workflows/{ci.yml,nightly.yml}
├── Makefile  Procfile  Procfile.prod  Procfile.ci  Brewfile
├── pyproject.toml  uv.lock  .python-version  .env.example
├── .pre-commit-config.yaml  .gitleaks.toml  .gitignore (.env, .data/, db/seeds/generated/)
└── README.md                             # clone → healthy path (SC-000-01)
```

### Source code: benefit-fe

```text
benefit-fe/
├── src/
│   ├── api/{client.ts,errors.ts,queryClient.ts,auth.ts,health.ts}
│   ├── api/generated/schema.d.ts         # openapi-typescript output; never hand-edited
│   ├── app/{router.tsx,AppShell.tsx,RequireRole.tsx}
│   ├── components/{SyntheticBanner.tsx,ErrorState.tsx,ui/*}
│   ├── features/auth/SignInPage.tsx      # + ForbiddenPage, NotFoundPage, placeholder /caseworker, /applicant
│   └── lib/{env.ts,time.ts}
├── e2e/
│   ├── playwright.config.ts  auth.setup.ts  fixtures.ts  pages/
│   ├── sign-in.spec.ts
│   └── {mismatch-request-info,restart-resume,missed-deadline-override,automatic-renewal,
│        renewal-one-document,applicant-blocked-other-household}.spec.ts   # test.fixme, pending
├── openapi/{openapi.json,BE_COMMIT}
├── scripts/{gen-api.mjs,check-api.mjs,ci/resolve-sibling-ref.sh}
├── .github/workflows/{ci.yml,nightly.yml}
├── package.json  pnpm-lock.yaml  .npmrc  .nvmrc  eslint.config.js  .prettierrc
├── tsconfig*.json (strict)  vite.config.ts (proxy /api, Tailwind, Vitest TZ)  components.json
└── .env.example
```

**Structure decision**: Use the layout in `project-rules/backend-architecture.md` (BA-1) and `frontend-ui.md`. Each lane's files are changed in that lane's own commits (BA ownership). `packages/domain` and `db/migrations/versions/0001_baseline.py` go in the Day 1 contracts PR.

## Lane plans

### Platform & UI (lead): benefit-be `apps/api/`, `packages/platform/`, setup; all of benefit-fe

**Scope**
- Scaffold fixes (R1).
- `packages/platform/*`: settings, clock, logging, errors, resilience, auth, audit, health, and the `synthetic.py` document-stamping helpers. No business logic.
- `apps/api` routers for auth and health.
- Makefile, the three Procfiles, Brewfile, pre-commit, CI, README.
- In benefit-fe: the app shell, sign-in, role guards, the SYNTHETIC banner, the generated client, and the e2e harness with six pending journeys.

**Provides**:
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `GET /health`, `GET /ready` under `/api/v1` ([contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml))
- `ErrorEnvelope`
- `Settings`
- `configure_logging`, `mask_pii`
- `call_with_retry`
- `issue_user_token`, `issue_system_credential`, `verify_system_credential`
- `AuditWriter`
- `serve_health`, readiness probes
- `stamp_pdf`, `stamp_image`, `stamp_text`, `is_marked`, which 003 seeds and 011 notices call (R24)

**Needs**:
- From K&D: the `users`, `households`, `audit_log` and `_meta` collections with their validators; the scoped repository helpers; the reset entry point; the fake embedder.
- From Agents: the provider factory and `LLM_MODE`.
- From Workflows: the worker health server and the credential minting call site.

**Rules most at risk**

| Rule | Risk | How the plan avoids it |
|---|---|---|
| PL-1 | Routes outside `/api/v1` | Health moves under `/api/v1` |
| PL-5 / PL-6 | The two token types accepted interchangeably | Separate keys plus `typ` and `aud` checks |
| PL-7 | A route without a test that each wrong role is rejected | A role-rejection test for every route, plus a test that walks every route |
| PL-11 | Uvicorn logs not masked | One structlog pipeline |
| PL-12–14 | Processes or tools left outside the standard setup | Every process in a Procfile, tools pinned, `make doctor`, pre-commit |
| PL-3 / FR-000-26 | API contract and generated client drifting apart | `openapi-check` plus the cross-repo comparison |
| BA-3 / BA-7 | Wrong import direction; `temporalio` used outside the apps | Shared code in `packages/platform`; the Temporal probe lives in `apps/*` |
| FE-3 / FE-4 / FE-6 / FE-10 / FE-11 / FE-12 / FE-13 | Frontend rules broken | Generated client, data access through `src/api` hooks, `RequireRole`, every page has loading, empty and error states, ESLint and Prettier, Playwright, synthetic fixtures |

### Workflows: benefit-be `apps/worker/`

**Scope**
- Worker `main.py` start-up order. Temporal being down is reported as "not ready", not as a crash.
- Health server on port 8001.
- Interceptors that bind `workflow_id`, `case_id` and `request_id`.
- `policies.py` presets (R9).
- `workflows/calendar.py`, a Chicago date from `workflow.now()`, with the zone passed through the sandbox.
- A `SmokeWorkflow` skeleton. 001 owns `CaseWorkflow`.
- `activities/agent_step.py` mints the system credential **at the start of each attempt**, with `exp` equal to the start-to-close timeout. The credential is never returned, stored in history or logged (R6).

**Provides**:
- worker `/health` and `/ready`
- the workflow ID format `case-{case_id}` (TW-3)
- activity presets

**Needs**:
- `Settings`, `configure_logging` and `issue_system_credential` from Platform
- `SystemCredentialClaims` and `HealthReport` from domain

**Rules most at risk**:
- TW-1: the zone is passed through; no environment or clock reads.
- TW-2 / BA-4: minting happens only in activities.
- TW-10: an AST test checks that every activity call uses a preset.
- TW-11: a fresh credential for each attempt.
- TW-12: dependencies are built once in `main.py`.
- TW-17: `workflow.logger` inside workflows, structlog in activities.

### Agents: benefit-be `packages/agents/`

**Scope**
- `llm/factory.py` is **the only module that imports a provider SDK**. It returns:
  - `ChatAnthropic` or `ChatBedrockConverse`, depending on `LLM_PROVIDER`
  - `ReplayChatModel` when `LLM_MODE` is `recorded` or `fake`
- The client is cached once per process.
- No temperature or top_p.
- A `structured()` helper uses native JSON-schema output and never forces tool choice.
- `llm/fake.py` holds `ReplayChatModel`. Fixtures are keyed by prompt id, version and input fingerprint. A missing fixture fails with a clear error.
- `llm/pricing.py` works out cost from `LLM_PRICE_*`.
- `tracing.py`:
  - instruments with OpenInference, lazily inside the factory (BA-4)
  - tags each run with `agent_run_context(case_id, workflow_id, …)`
  - exports through a deny-by-default `MaskingSpanExporter`
  - uses a bounded `BatchSpanProcessor`, so a Phoenix outage never fails a run
- The live smoke test (`live_llm`) checks five things on the provider that is configured.

**Provides**:
- `get_chat_model()`, `agent_run_context()`
- the domain models `AgentRunContext` and `AgentRunUsage`
- the keyword-only `tool_credential` argument on agent entry points (contracts PR)

**Needs**:
- Settings fields from Platform
- `mask_pii()` from Platform
- the Phoenix Procfile entry and the degraded readiness probe

**Rules most at risk**:
- AG-5 / VII: ruff TID251 bans the SDK imports everywhere else.
- AG-6, AG-7, AG-9: covered by unit tests.
- AG-15: covered by `agent_run_context`.
- AG-16 / FR-000-20: an autouse fixture forces `fake`.

### Knowledge & data: benefit-be `db/`, `packages/rag/`, `analytics/`

**Scope**
- `db/mongo/provision.py` (run by `make mongo-up`) initiates the replica set and creates the users `benefit_owner` and `benefit_app` and the `auditAppend` role.
- `db/migrate.py` and the `0001_baseline` migration (contracts PR) create, each with a working `downgrade`:
  - `users`, with a validator that every applicant has a household, and a case-insensitive unique index on `username`
  - `households` (stub)
  - `audit_log`, with a closed-field validator (no free-text field) and indexes
  - `_meta`, with the synthetic marker validator
  - the other collections, validators and indexes from `specs/README.md`
- A scoped repository helper (R16) that every household-scoped query goes through.
- `db/seeds/` creates the four demo accounts, hashing `DEMO_PASSWORD` with argon2id at seed time. Nothing secret is committed.
- The seed generator stamps every generated document with `packages/platform/synthetic.py` (R24). In 000 that is a one-page sample pay stub, so the stamping test has something to check. 003 adds the full document set.
- `db/seeds/reset.py` has a guard and runs: migrations down and up, DuckDB export and dbt, seed, marker.
- `FakeEmbedder` is a 1024-dimension deterministic hash, and `FakeReranker` scores by token overlap. They are selected by `EMBEDDER` and `RERANKER`, and the ML libraries go in an optional `ml` uv group.
- `analytics/` adds the `meta.dataset_metadata` dbt model and its test.

**Provides**:
- the collections, validators, indexes and database users
- the scoped repository helper that applies the household filter
- the reset entry point
- the `Embedder` and `Reranker` factory

**Needs**:
- the settings `MONGO_URL_APP`, `MONGO_URL_OWNER`, `MONGO_DB`, `DUCKDB_PATH`, `DEMO_PASSWORD`, `EMBEDDER`, `RERANKER`
- the argon2id hasher from Platform

**Rules most at risk**:
- KD-11: a single baseline, with the downgrade exercised on every reset.
- KD-12: the `auditAppend` role, tested by trying update, delete and drop as the app user.
- KD-10: transactions need the replica set from `make mongo-up`.
- KD-13 / PR-3: synthetic seeds only.
- database.md: validators, unique indexes, the household filter in every query, and no filter built from raw input.

## Test plan (requirement → tests)

**How tests are selected and run**
- Every test gets exactly one level marker (`unit`, `workflow`, `contract`, `integration`, `api` or `stack`) from its directory, applied in `tests/conftest.py` with `--strict-markers`. A test cannot silently drop out of a CI job. `test_every_collected_test_has_exactly_one_level_marker` enforces this.
- `make test` runs everything that needs no running stack. `api` and `stack` tests need the stack (`make dev`, or `Procfile.ci` in CI), so in CI they run in the `e2e` job. The `integration` job runs `-m integration` only.
- Work goes one test at a time, red then green then refactor (constitution V). The task groups are checklists, not a batch (see the header of [tasks.md](tasks.md)).

All test names start with the FR ID (constitution V, `testing.md`). Paths are relative to `tests/` in benefit-be unless the row says `fe:`.

| Requirement | Tests (level) |
|---|---|
| FR-000-01 | `stack/test_stack_health.py::test_FR_000_01_every_component_ready` (marker `stack`; runs in the CI `e2e` job against `Procfile.ci`); quickstart §1 |
| FR-000-02 | `db/seeds/test_reset.py::test_FR_000_02_reset_restores_seeded_counts_and_markers` (integration) |
| FR-000-03 | `packages/platform/test_settings.py::test_FR_000_03_env_example_lists_every_setting` (unit) |
| FR-000-04 | `…::test_FR_000_04_missing_setting_refuses_start_names_setting`; `apps/worker/test_main.py::test_FR_000_04_worker_missing_setting_exits_naming_it` (unit) |
| FR-000-05 | `apps/api/dependencies/test_authz.py::test_FR_000_05_supervisor_allowed_where_caseworker_allowed` (parametrized over roles, unit); `db/seeds/test_users.py::test_FR_000_05_seed_creates_each_role`; fe: `RequireRole.test.tsx` |
| FR-000-06 | `contract/test_every_route_protected.py::test_FR_000_06_every_non_health_route_requires_session` (unit/contract); `db/test_rls.py::test_FR_000_06_unset_role_sees_no_rows` (integration); fe e2e `sign-in.spec.ts` |
| FR-000-07 | `packages/platform/test_tokens.py::test_FR_000_07_session_expires_after_configured_ttl` (FixedClock); `apps/api/routers/test_auth.py::test_FR_000_07_expired_session_returns_session_expired`; fe: `client.test.ts` |
| FR-000-08 | `apps/api/test_errors.py::test_FR_000_08_validation_error_has_code_message_fields`, `…_unexpected_error_returns_generic_message_with_reference`; `api/test_auth.py` (error shape, no leak) |
| FR-000-09 | `apps/api/routers/test_health.py::test_FR_000_09_*`; `integration/test_readiness.py::test_FR_000_09_mongo_down_not_ready_health_ok`; `apps/worker/test_health.py::test_FR_000_09_worker_ready_false_health_true_when_temporal_down` |
| FR-000-10 | `packages/platform/test_logging.py::test_FR_000_10_log_includes_request_case_workflow_ids`; `apps/worker/test_interceptors.py::test_FR_000_10_activity_log_includes_case_and_workflow_id` |
| FR-000-11 | `packages/platform/test_logging.py::test_FR_000_11_personal_data_masked` (parametrized keys and patterns) |
| FR-000-12 | `packages/agents/llm/test_factory.py::test_FR_000_12_{anthropic,bedrock}_provider_builds_*`, `…_unknown_provider_lists_allowed_values`, `…_provider_sdk_imported_only_in_factory` |
| FR-000-13 | `packages/platform/test_resilience.py::test_FR_000_13_*`; `packages/agents/llm/test_factory.py::test_FR_000_13_client_has_timeout_and_bounded_retries`; `apps/worker/test_policies.py::test_FR_000_13_every_activity_call_uses_policy_preset` (AST) |
| FR-000-14 | `db/test_markers.py::test_FR_000_14_each_store_has_synthetic_marker` (integration); dbt test; `packages/platform/test_synthetic.py::test_FR_000_14_{pdf,image,text}_stamp_is_visible_and_detected`, `…_stamp_does_not_cover_body`; `db/seeds/test_generated_documents.py::test_FR_000_14_every_generated_document_is_marked`; fe: `SyntheticBanner.test.tsx` |
| FR-000-16 | `contract/test_ci_workflow.py::test_FR_000_16_ci_runs_every_required_job`; fe: `src/ci/ciWorkflow.test.ts`; quickstart §9 throwaway-PR check |
| FR-000-17 | `integration/conftest.py` harness (reset before run, `LLM_MODE=fake`); `apps/worker/test_smoke_integration.py::test_FR_000_17_worker_runs_smoke_against_local_temporal` |
| FR-000-18 | `contract/test_openapi.py::test_FR_000_18_live_schema_matches_committed_and_names_diff`; `contract/test_tool_schemas.py` harness (005 adds snapshots); fe: `api:check` |
| FR-000-19 | fe e2e: six journey files with `test.fixme` and a `pending` annotation; `sign-in.spec.ts` |
| FR-000-20 | `conftest.py` autouse guard: `test_FR_000_20_live_model_refused_in_tests`; `packages/agents/llm/test_fake.py::test_FR_000_20_*` |
| FR-000-21 | `packages/platform/test_passwords.py::test_FR_000_21_hash_is_argon2id_and_verifies`; `db/seeds/test_users.py::test_FR_000_21_seed_refuses_without_demo_password`; `apps/api/routers/test_auth.py::test_FR_000_21_*` |
| FR-000-22 | `packages/platform/test_tokens.py::test_FR_000_22_credential_rejected_for_other_case`, `…_has_no_user_role`, `…_rejected_after_expiry`; `apps/api/routers/test_auth.py::test_FR_000_22_system_credential_rejected_on_user_routes`; `apps/worker/activities/test_agent_step.py::test_FR_000_22_new_credential_per_attempt_not_in_result_or_logs` |
| FR-000-23 | `apps/api/routers/test_auth.py::test_FR_000_23_sign_in_success_and_failure_audited_without_username`; `db/test_audit_log.py::test_FR_000_23_app_role_update_delete_truncate_denied`, `…_trigger_blocks_owner_update`, `…_audit_schema_has_no_free_text_column` |
| FR-000-24 | `integration/test_versions.py::test_FR_000_24_store_major_versions_match_local`; `packages/rag/test_fake_embedder.py::test_FR_000_24_fake_embedder_deterministic` (+ hypothesis) |
| FR-000-25 | `scripts/ci/resolve-sibling-ref.sh` exercised in the e2e job and checked in its summary; `tests/scripts/test_resolve_sibling_ref.py::test_FR_000_25_falls_back_to_main` |
| FR-000-26 | `contract/test_openapi.py::test_FR_000_26_committed_openapi_file_is_current_and_sorted`; fe: `src/api/generated.test.ts`; `make openapi-check`; fe `api:check`; fe CI contract job compares against the benefit-be branch |
| FR-000-27 | `packages/platform/test_clock.py::test_FR_000_27_chicago_date_across_utc_midnight_and_dst`; `apps/worker/workflows/test_calendar.py`; fe: `time.test.ts` |
| FR-000-28 | `packages/agents/test_tracing.py::test_FR_000_28_spans_tagged_with_case_and_workflow_id`, `…_span_records_model_provider_tokens_and_cost`, `…_exported_spans_contain_no_personal_data`, `…_exporter_down_agent_run_succeeds`, `…_tracing_disabled_installs_no_exporter`; `integration/test_readiness.py::test_FR_000_28_tracing_down_reports_degraded` |

**Workflow tests (TW-13/14/16)** for `SmokeWorkflow`:
- a time-skipping happy path
- a replay against `histories/smoke_v1.json`
- resume after a worker restart

**Role-rejection tests (PL-7)** for every new route. `/auth/me` and `/auth/logout` reject anonymous callers and system credentials. A parametrized `require_roles` probe covers all three roles.

## Delivery order

1. **Day 1 contracts PR** (all lanes; R23):
   - `packages/domain` models (data-model.md)
   - `0001_baseline` (K&D)
   - the OpenAPI contract
   - the `tool_credential` signature change
   - add `openapi/` to the BA-1 layout tree
2. **benefit-be `feature/000-platform-foundations`**, one commit series per lane:
   1. scaffold move and tooling
   2. `packages/platform`
   3. `db/` bootstrap, seeds and reset
   4. `apps/api`
   5. `apps/worker`
   6. `packages/agents/llm` and tracing
   7. Makefile, Procfiles and CI
3. **benefit-fe `feature/000-platform-foundations`**, linked PR:
   1. toolchain switch
   2. generated client
   3. shell and sign-in
   4. e2e harness
   5. CI
4. **009 (FR-009-02)** turns on branch protection with these job names as required checks, before the first feature PR.

## Remaining inputs (non-blocking)

These are needed from people. Details are in [research.md](research.md), "Inputs still needed from people".

| # | Input | From | Blocks |
|---|---|---|---|
| P1 | Bedrock inference-profile ID and region for `claude-opus-5-5` | The team member with Bedrock access, set in their own `.env` | Only `make smoke-ai` on Bedrock (SC-000-04) |
| P2 | Branch protection with these CI job names as required checks, in both repos | A repo admin, through 009 (FR-009-02) | Merge blocking (FR-000-16, SC-000-06). Must be in place before the first feature PR. |
| P3 | Tick the 000 items under "Spec review round 2" in `specs/README.md` | All three team members, in the contracts PR review | Merging the contracts PR |
| P4 | Agree the order of the contracts PR (`0001_baseline`) and the 000 sign-in work | The team, on Day 1 morning | Merging the sign-in work |
| P5 | Approve the draft constitution amendment 2.0.0 (MongoDB as the only database, no row-level security) | All three team members, by PR | Merging any MongoDB-only database work, and the changes to `project-rules/` and `specs/README.md` |

## Early verification tasks

These assumptions have not been checked. `/speckit-tasks` should schedule each as an early task with the fallback from [research.md](research.md) R26.

- **V1**: Phoenix can delete a project through its REST API.
- **V2**: The Homebrew `mongod` starts as an authenticated single-node replica set, and `provision.py` can create the users.
- **V3**: ESLint 10 works with typescript-eslint 8.72.
- **V4**: Both LangChain provider packages give native structured output.
- **V5**: The Temporal CLI version matches between Homebrew and CI.
- **V6**: The replay-test history is recorded after the smoke workflow passes (an ordering constraint).

## Complexity Tracking

No constitution violations to justify. New tools are justified in the "New tools and services" table above.
