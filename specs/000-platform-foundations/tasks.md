---
description: "Task list for 000 Platform Foundations"
---

# Tasks: Platform Foundations

**Input**: Design documents from `specs/000-platform-foundations/`: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md).

**Tests**: Required. Constitution V (test-first, non-negotiable) says every `FR-000-xx` must have at least one test named after it. In each phase, the test tasks come first and must **fail** before the implementation task that follows them.

**Red-green-refactor, one test at a time** (constitution V, `project-rules/testing.md`): the "Tests for User Story N" blocks are checklists, not a batch to write up front. Take **one** test (one bullet), write it, watch it fail, write the code that makes it pass, refactor with everything green, then take the next. Never have more than one failing test at a time. A task that lists several tests is several red-green cycles, and each cycle should be its own commit. Python tests are named `test_FR_000_<nn>_<scenario>_<expected>`. Vitest and Playwright tests start with `FR-000-<nn>:`.

**Organization**: Tasks are grouped by user story. P1 stories come first in spec order (US1 → US2 → US5), then the P2 stories (US3 → US4).

**Lanes**: Each task names its owning lane, so commits stay split by lane (BA ownership):
- **[PUI]**: Platform & UI
- **[WF]**: Workflows
- **[AG]**: Agents
- **[KD]**: Knowledge & data
- **[ALL]**: Day 1 contracts PR, reviewed by every lane

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: The user story the task belongs to (US1 to US5)

## Path conventions

- Paths are relative to `repos/`: `benefit-be/...` (Python backend) and `benefit-fe/...` (React SPA).
- Metarepo paths start with `specs/` or `project-rules/`.
- Backend tests mirror the source tree under `benefit-be/tests/` (BA-9). Frontend tests sit next to their source as `*.test.tsx`/`*.test.ts`. End-to-end tests live in `benefit-fe/e2e/`.
- Settings names, error codes, log fields, make targets and ports are defined in the [contracts/](contracts/) files. Tasks name the file instead of repeating it.

---

## Phase 1: Setup (shared infrastructure)

**Purpose**: Get both scaffolds onto the layout and tooling the rules require (research R1–R3), and check the toolchain assumptions (R26).

- [X] T001 Sync both clones with the `sync-repos` skill, then create branch `feature/000-platform-foundations` from `main` in `benefit-be` and in `benefit-fe` [PUI]
- [X] T002 Restructure `benefit-be` to the BA-1 layout [PUI]:
  - `git mv benefit-be/app benefit-be/apps/api`, keeping `routers/`, `services/` and `repositories/`.
  - Create empty `__init__.py` packages: `benefit-be/apps/__init__.py`, `apps/worker/{__init__,workflows/__init__,activities/__init__}.py`, `packages/__init__.py`, `packages/{domain,platform,platform/auth,agents,agents/llm,rag}/__init__.py`.
  - Create folders `packages/agents/prompts/`, `db/`, `scripts/ci/` and `openapi/`.
  - `git mv benefit-be/tests/test_health.py benefit-be/tests/apps/api/routers/test_health.py`, then add `__init__.py` files so `tests/` mirrors the source tree.
- [X] T003 Replace `benefit-be/requirements.txt` with a uv project in `benefit-be/pyproject.toml` (R2, PR-4) [PUI]:
  - `requires-python = ">=3.12,<3.13"`.
  - Pin each runtime dependency exactly (`==`): fastapi, uvicorn[standard], pydantic, pydantic-settings, pyjwt, argon2-cffi, structlog, httpx, temporalio, pymongo, numpy, tzdata, langchain-core, langchain-anthropic, langchain-aws, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-http, openinference-instrumentation-langchain, pypdf, reportlab, pillow, duckdb, dbt-duckdb.
  - `[dependency-groups].dev`: pytest, pytest-asyncio, pytest-playwright, hypothesis, mypy, ruff, pip-audit, pre-commit, honcho.
  - `[dependency-groups].ml`: torch and sentence-transformers. This group is optional and not installed in CI.
  - Add `benefit-be/.python-version` containing `3.12`.
  - Run `uv lock` and commit `benefit-be/uv.lock`. Delete `requirements.txt`.
- [X] T004 [P] Configure ruff and mypy in `benefit-be/pyproject.toml` [PUI]:
  - ruff: `line-length = 100`; rule sets `E,F,I,B,UP,S,ASYNC,TID`.
  - `flake8-tidy-imports.banned-api` bans `anthropic`, `langchain_anthropic`, `langchain_aws` and `boto3` (AG-5, R8). Allow them only in `packages/agents/llm/factory.py` with a per-file ignore.
  - mypy: `strict = true` with the `pydantic.mypy` plugin.
- [X] T005 [P] Configure pytest in `benefit-be/pyproject.toml` [PUI]:
  - Markers: `unit`, `workflow`, `contract`, `integration`, `api`, `stack`, `live_llm`.
  - `addopts = "--strict-markers -m 'not live_llm'"` and `asyncio_mode = "auto"`.
  - In `benefit-be/tests/conftest.py`, add `pytest_collection_modifyitems` that applies a marker from the test's directory, so no test depends on someone remembering a decorator: `tests/contract/` → `contract`; `tests/integration/`, `tests/db/` and any `integration`-named test → `integration` (explicit marks win); `tests/api/` → `api`; `tests/stack/` → `stack`; `tests/**/workflows/` and `tests/apps/worker/**/test_smoke*` → `workflow`; every other test → `unit`. A test that has an explicit marker keeps it and gets no extra one. Add `benefit-be/tests/test_marker_assignment.py::test_every_collected_test_has_exactly_one_level_marker`, which fails when a test ends up with none or several of `unit`, `workflow`, `contract`, `integration`, `api` and `stack`.
  - Create `benefit-be/tests/conftest.py` with an autouse fixture that sets `APP_ENV=test`, `LLM_MODE=fake`, `EMBEDDER=fake`, `RERANKER=fake` and `TRACING_ENABLED=false`.
  - Add a `settings` fixture that builds `Settings` from a dict.
- [X] T006 [P] Extend `benefit-be/.gitignore` with `.env`, `.data/`, `db/seeds/generated/`, `.venv/`, `.mypy_cache/` and `.pytest_cache/`. Only `.env.example` is committed (FR-000-03). [PUI]
- [X] T007 [P] Create `benefit-be/Brewfile` (PL-13) [PUI]:
  - `tap "mongodb/brew"`
  - `brew` entries: `python@3.12`, `uv`, `node@24`, `pnpm`, `mongodb/brew/mongodb-community@8.0`, `mongosh`, `temporal`, `gitleaks`
- [X] T008 Verify V2 (the Homebrew `mongod` runs as an authenticated single-node replica set) [KD]:
  - Install `mongodb-community@8.0` and `mongosh`. Start `mongod` once by hand with `--replSet rs0 --keyFile <file> --auth`, initiate the replica set, create a user over the localhost exception, and check that a multi-document transaction works.
  - Record the result under R26 in `specs/000-platform-foundations/research.md`.
  - If the localhost exception blocks `replSetInitiate`, use the R26 fallback: start without `--auth`, initiate and provision, then restart with `--auth`.
- [X] T009 Verify V5 (Temporal CLI version) [WF]:
  - Record `temporal --version` as `TEMPORAL_CLI_VERSION` at the top of `benefit-be/Makefile`.
  - Use the same version for the CI install step in a later task.
  - Note the result under R26 in `specs/000-platform-foundations/research.md`.
- [X] T010 Switch `benefit-fe` to pnpm (R3, FE-1, PR-4) [PUI]:
  - Delete `benefit-fe/package-lock.json`.
  - In `benefit-fe/package.json`: add `"packageManager": "pnpm@11.20.0"` and `"engines": {"node": ">=24 <25"}`; remove every `^` and `~`; change `typescript` to `5.9.3`.
  - Add `benefit-fe/.npmrc` with `save-exact=true` and `engine-strict=true`, and `benefit-fe/.nvmrc` containing `24`.
  - Run `pnpm install` and commit `benefit-fe/pnpm-lock.yaml`.
- [X] T011 Replace oxlint with ESLint and Prettier (FE-11) [PUI]:
  - Delete `benefit-fe/.oxlintrc.json` and the `oxlint` dependency.
  - Add `benefit-fe/eslint.config.js` (flat config: typescript-eslint `strictTypeChecked`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`; ignore `src/api/generated/**`).
  - Add `benefit-fe/.prettierrc` and `benefit-fe/.prettierignore`.
  - Add scripts `lint`, `format:check` and `typecheck` (`tsc -b --noEmit`).
  - **Verify V3**: if ESLint 10 doesn't work with typescript-eslint 8.72, pin `eslint` 9.x. Record the result under R26 in `specs/000-platform-foundations/research.md`.
- [X] T012 [P] Turn on strict TypeScript in `benefit-fe/tsconfig.app.json` and `benefit-fe/tsconfig.node.json`: `"strict": true`, `"noUncheckedIndexedAccess": true`, `"exactOptionalPropertyTypes": true` (FE-1). [PUI]
- [X] T013 Add the frontend runtime stack [PUI]:
  - Install `react-router`, `@tanstack/react-query`, `openapi-fetch`, `tailwindcss`, `@tailwindcss/vite`.
  - Run `pnpm dlx shadcn init` to create `benefit-fe/components.json` and `benefit-fe/src/components/ui/`.
  - Replace the Vite demo: delete `src/App.tsx`, `src/App.css` and `src/assets/*`, and reduce `src/index.css` to the Tailwind import.
- [X] T014 Configure `benefit-fe/vite.config.ts` [PUI]:
  - Add the Tailwind plugin.
  - Proxy `/api` to `process.env.API_BASE_URL ?? 'http://localhost:8000'` under both `server.proxy` and `preview.proxy` (R4: same origin).
  - Configure Vitest: `environment: 'jsdom'`, `setupFiles: ['src/test/setup.ts']`, `env: { TZ: 'America/Chicago' }`.
  - Install `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event` and `@testing-library/jest-dom`.
  - Create `benefit-fe/src/test/setup.ts`.
- [X] T015 [P] Create `benefit-fe/.env.example` with the frontend settings table from [contracts/settings.md](contracts/settings.md). Leave `E2E_PASSWORD` blank. Add `.env` and `e2e/.auth/` to `benefit-fe/.gitignore`. [PUI]

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: The shared contracts (Day 1 contracts PR, R23) plus the settings, logging, error, API-factory, database-baseline and OpenAPI-client infrastructure that every story builds on.

**⚠️ CRITICAL**: No user story work starts until this phase is merged.

### Shared contracts: `packages/domain` and the metarepo (Day 1 contracts PR)

- [X] T016 [P] Create `benefit-be/packages/domain/auth.py` as specified in [data-model.md](data-model.md). It imports nothing else from this repo (BA-6). [ALL]
  - `Role(StrEnum)`: `applicant`, `caseworker`, `supervisor`.
  - `UserPublic{id: UUID, username: str, display_name: str, role: Role, household_id: UUID | None}`.
  - `Principal{user_id: UUID, role: Role, household_id: UUID | None, session_expires_at: datetime}`.
  - `SystemCredentialClaims`: `typ: Literal["system"]`, `aud: Literal["agent-tools"]`, `sub: Literal["system:agent"]`, `case_id: UUID`, `workflow_id: str`, `step: str`, `iat: int`, `exp: int`, `jti: str`. It has **"no `role` claim"**.
  - `LoginRequest`: username `minLength 1, maxLength 64, pattern ^[A-Za-z0-9_.-]+$`; password `minLength 1, maxLength 128`; `extra="forbid"`.
  - `SessionInfo{user: UserPublic, expires_at: datetime}`.
- [X] T017 [P] Create `benefit-be/packages/domain/audit.py` [ALL]:
  - `AuditAction` with exactly these values: `sign_in`, `access_refused`, `caseworker_action`, `demo_clock_action`, `redetermination_started_on_demand`, `metrics_refreshed`.
  - `ActorType`: `user`, `system`, `anonymous`.
  - `AuditOutcome`: `success`, `failure`, `refused`.
  - `AuditLogEntry` with the fields from the data-model "Audit log entry" table: `actor_type`, `actor_id`, `actor_role`, `action`, `target_type`, `target_id`, `outcome`, `reason_code`, `reference_id`, `occurred_at`.
- [X] T018 [P] Create `benefit-be/packages/domain/errors.py` [ALL]:
  - `ErrorCode(StrEnum)` with exactly `auth.required`, `auth.session_expired`, `auth.invalid_credentials`, `auth.forbidden`, `not_found`, `conflict`, `validation_failed`, `internal_error`, `dependency_unavailable`.
  - `FieldError{field, message, type}`.
  - `ErrorBody{code, message, fields: list[FieldError], reference_id}` with `extra="forbid"`.
  - `ErrorEnvelope{error: ErrorBody}`.
- [X] T019 [P] Create `benefit-be/packages/domain/health.py` [ALL]:
  - `HealthReport{component, status: Literal["ok"], version, synthetic_data: Literal[True]}`.
  - `CheckStatus` (`ok`, `down`, `degraded`) and `ReadinessStatus` (`ready`, `degraded`, `not_ready`).
  - `ReadinessCheck{name, status, required: bool}`.
  - `ReadinessReport{component, status, checks}` with a `from_checks(component, checks)` classmethod:
    - `not_ready` if any required check is `down`
    - otherwise `degraded` if any check is not `ok`
    - otherwise `ready`
- [X] T020 [P] Create `benefit-be/packages/domain/dataset.py` (`DatasetMetadata{synthetic: Literal[True], seed: int, generator_version: str, generated_at: datetime}`) and `benefit-be/packages/domain/agent_run.py` (`AgentRunContext{case_id, workflow_id}`, `AgentRunUsage{model, provider, input_tokens, output_tokens, cost_usd, duration_ms, recorded: bool}`). [ALL]
- [X] T021 [P] Write `benefit-be/tests/packages/domain/test_health.py::test_readiness_report_status_derived_from_checks`. Parametrize over: required down → `not_ready`; only optional down → `degraded`; all ok → `ready`. [ALL]
- [X] T022 [P] Contract changes in the metarepo (contracts PR) [ALL]:
  - In `specs/README.md` under "Interfaces between lanes", add the keyword-only `tool_credential: str` to the agent entry points, e.g. `verify_documents(case_id, *, tool_credential)` (R6).
  - In `project-rules/backend-architecture.md`, add `openapi/` and `scripts/` to the BA-1 layout tree.

### Platform core (`packages/platform`)

- [X] T023 [P] Write the failing settings tests in `benefit-be/tests/packages/platform/test_settings.py` [PUI]:
  - `test_FR_000_04_missing_setting_refuses_start_names_setting`: exit code 2; stderr names the setting and never contains the value.
  - `test_FR_000_12_unknown_llm_provider_lists_allowed_values`: prints `allowed: anthropic, bedrock`.
  - `test_FR_000_03_env_example_lists_every_setting`: the key set in `.env.example` equals the fields of `Settings`.
  - A parametrized test of the cross-field rules from [contracts/settings.md](contracts/settings.md):
    - `SESSION_SECRET != SYSTEM_CREDENTIAL_SECRET`
    - live anthropic requires `ANTHROPIC_API_KEY`
    - live bedrock requires `AWS_REGION` and `BEDROCK_MODEL_ID`
    - `APP_ENV=test` requires fake modes and tracing off
- [X] T024 Implement `benefit-be/packages/platform/settings.py` [PUI]:
  - `Settings(BaseSettings)` with `extra="forbid"`, every field, type, default and allowed value in [contracts/settings.md](contracts/settings.md), `SecretStr` for secrets, `StrEnum` for choices, and the cross-field model validator.
  - `load_settings()` catches `ValidationError`, prints `setting <NAME>: <reason>; allowed: <values>` to stderr without the value, and calls `sys.exit(2)`.
- [X] T025 Create `benefit-be/.env.example` with every key from [contracts/settings.md](contracts/settings.md) and its default. Leave the secrets (`SESSION_SECRET`, `SYSTEM_CREDENTIAL_SECRET`, `DEMO_PASSWORD`, `ANTHROPIC_API_KEY`) blank, with a comment that `make setup` generates them. [PUI]
- [X] T026 [P] Write the failing clock tests in `benefit-be/tests/packages/platform/test_clock.py` (FR-000-27) [PUI]:
  - `test_FR_000_27_chicago_date_across_utc_midnight_and_dst`: 05:30 UTC counts as the previous Chicago day; check both 2026 DST boundaries.
  - `test_FR_000_27_days_between_counts_calendar_days`.
- [X] T027 Implement `benefit-be/packages/platform/clock.py` [PUI]:
  - A `Clock` protocol with `now() -> datetime` (UTC, aware), plus `SystemClock` and `FixedClock`.
  - `CHICAGO = ZoneInfo("America/Chicago")`.
  - `today(clock) -> date`, `to_local(dt)` and `days_between(a, b)`, all computed in Chicago time.
- [X] T028 [P] Write the failing logging test in `benefit-be/tests/packages/platform/test_logging.py`: `test_FR_000_10_log_includes_request_case_workflow_ids`. Bind the three IDs through contextvars, render one JSON line, and assert the fields `timestamp`, `level`, `event` and `component` from [contracts/logging.md](contracts/logging.md) are present. [PUI]
- [X] T029 Implement `benefit-be/packages/platform/logging.py` [PUI]:
  - `configure_logging(settings, component)`: a structlog JSON renderer to stdout (or console when `LOG_FORMAT=console`), with ISO UTC timestamps.
  - Merge contextvars, and expose `bind_context(**ids)` and `clear_context()`.
  - Route the stdlib, `uvicorn`, `temporalio` and `httpx` loggers through `ProcessorFormatter`.
  - Leave a processor slot for `mask_pii`, which US3 fills.
- [X] T030 [P] Write the failing error-format tests in `benefit-be/tests/apps/api/test_errors.py` [PUI]:
  - `test_FR_000_08_validation_error_has_code_message_fields`: POST `{}` to a probe route; expect 422 with `validation_failed`, `fields[].field == "body.username"`, input values not echoed, and `reference_id == X-Request-ID`.
  - `test_app_error_maps_to_status` (parametrized): each `ErrorCode` maps to the status in [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml).
- [X] T031 Implement `benefit-be/packages/platform/errors.py` with the `AppError` base class (`code`, `status`, `message`) and the subclasses `AuthRequired`, `SessionExpired`, `InvalidCredentials`, `Forbidden`, `NotFound`, `Conflict` and `DependencyUnavailable`. [PUI]
- [X] T032 Implement `benefit-be/apps/api/errors.py`: `register_error_handlers(app)` for `AppError`, `RequestValidationError` (mapped to `FieldError` without the input) and `StarletteHTTPException`. Every response is an `ErrorEnvelope` with the `X-Request-ID` header. The 500 handler comes in US3. [PUI]
- [X] T033 [P] Write the failing request-context test in `benefit-be/tests/apps/api/middleware/test_request_context.py` [PUI]:
  - `test_FR_000_10_request_id_generated_echoed_and_logged`: no header → a UUID is generated, echoed in `X-Request-ID`, and logged in `request.completed` with the route template.
  - `test_request_id_invalid_header_replaced`.
- [X] T034 Implement `benefit-be/apps/api/middleware/request_context.py` (pure ASGI middleware) [PUI]:
  - Accept an incoming `X-Request-ID` only if it is a valid UUID; otherwise generate `uuid4`.
  - Bind it with `bind_context(request_id=...)` and echo it in the response.
  - Log `request.completed` with `method`, `route` (the route template), `status` and `duration_ms`. Never log bodies or query strings.
- [X] T035 Rewrite `benefit-be/apps/api/main.py` as a `create_app(settings: Settings | None = None) -> FastAPI` factory [PUI]:
  - Load the settings, call `configure_logging(settings, "api")`, add the request-context middleware, call `register_error_handlers`, and mount every router under `/api/v1` (PL-1).
  - Drop the module-level `app` and the root `/health`.
  - Run with `uvicorn apps.api.main:create_app --factory`.

### Database baseline (Knowledge & data; Day 1 contracts PR)

- [X] T036 [P] Implement `benefit-be/db/mongo/provision.py` and the `mongo-up` and `mongo-down` targets (R13, R14) [KD]:
  - `provision.py` connects over the localhost exception, initiates replica set `rs0` if it isn't initiated, then creates the custom role `auditAppend` (privileges `insert` and `find` on `benefit_audit.audit_log` only), the user `benefit_owner` (the first user holds only `userAdminAnyDatabase`, because of the localhost exception; `dbOwner` on `benefit`, `benefit_audit` and their `_test` twins is granted after it authenticates) and the user `benefit_app` (`readWrite` on `benefit` and `benefit_test`, plus `auditAppend`). The audit log lives in its own database `benefit_audit` so `readWrite` never covers it. The passwords come from `MONGO_URL_OWNER` and `MONGO_URL_APP`. It is idempotent.
  - `make mongo-up`: create `.data/mongo/keyfile` if missing (`openssl rand -base64 756`, mode 400), start `mongod --replSet rs0 --keyFile ... --auth --bind_ip 127.0.0.1 --dbpath .data/mongo/db --fork --logpath .data/mongo/mongod.log` if it isn't already running, wait for it to accept connections, then run `provision.py`.
  - `make mongo-down`: shut it down with `mongod --shutdown --dbpath .data/mongo/db`.
- [X] T037 [P] Implement the migration runner `benefit-be/db/migrate.py` (KD-11) [KD]: `up(target)` and `down(target)` apply the scripts in `benefit-be/db/migrations/versions/` in order, each exposing `upgrade(db)` and `downgrade(db)`, and record applied versions in the `_migrations` collection (`_id` is the version, plus `applied_at`). Connect with `MONGO_URL_OWNER`. Command line: `python -m db.migrate up|down [version|base|head]`. Applying an already-applied version is a no-op.
- [X] T038 Write `benefit-be/db/migrations/versions/0001_baseline.py` with the collections for 000, following [data-model.md](data-model.md) exactly [KD]. `audit_log` goes in the database `MONGO_AUDIT_DB`, the rest in `MONGO_DB`. Every collection gets a `$jsonSchema` validator with `additionalProperties: false`. `downgrade` drops everything the migration created (KD-11).
  - **`users`**:
    - `_id` UUID, `username` string (1–64 chars, pattern `^[a-z0-9_.-]+$`), `display_name` string, `password_hash` string matching `^\$argon2id\$`, `role` enum `applicant`, `caseworker`, `supervisor`, `household_id` UUID or null, `created_at` date. All required except `household_id`.
    - Validator rule: **"required and non-null when `role == "applicant"`, absent or null otherwise"**.
    - Unique index on `username` with collation `{locale: "en", strength: 2}`.
  - **`households`**: `_id` UUID and `created_at` date.
  - **`audit_log`**:
    - Fields: `occurred_at` date (required), `actor_type` enum `user`, `system`, `anonymous` (required), `actor_id` string (max 128), `actor_role` enum, `action` enum of the 6 values (required), `target_type` string (max 128), `target_id` string (max 128), `outcome` enum `success`, `failure`, `refused` (required), `reason_code` enum `invalid_credentials`, `role_not_allowed`, `wrong_household`, `wrong_case`, `credential_expired`, `reference_id` string (max 128, required).
    - **"no free-text or nested-object field"**: no object or array fields, and every string is length-capped.
    - Indexes: `{target_type: 1, target_id: 1, occurred_at: 1}` and `{occurred_at: 1}`.
  - **`_meta`**: validator requires `synthetic: true`, plus `seed` int, `generator_version` string and `generated_at` date.
  - **The other collections** named in `specs/README.md` ("Shared contracts outline"), each created empty with a validator that at least requires `_id`, and `household_id` and `case_id` where the collection is household-scoped (the scoped ones are `documents`, `extractions`, `agent_runs`, `notice_drafts`, `tool_calls`, `cases`, `case_events`, `review_tasks`, `caseworker_actions`, `determinations`, `household_members`, `household_snapshots`, `coverage_periods`, `outbox`), with indexes `{case_id: 1, created_at: -1}` and `{household_id: 1}` on those; unique `{draft_id: 1, revision: 1}` on `notice_drafts`; unique `{finding_id: 1}` on `eval_overrides`. The owning features tighten these validators in their own migrations.
- [X] T039 Add `doctor` and `setup` to `benefit-be/Makefile` so MongoDB can run before anything else needs it [PUI]:
  - `doctor` checks the Brewfile tools and versions, that `.env` exists and that `BENEFIT_FE_DIR` is a checkout, and exits non-zero listing what is missing.
  - `setup` copies `.env.example` to `.env` if it is missing and fills `SESSION_SECRET`, `SYSTEM_CREDENTIAL_SECRET`, `DEMO_PASSWORD` and the two MongoDB passwords (then builds `MONGO_URL_OWNER` and `MONGO_URL_APP` from them) using `python -c "import secrets; print(secrets.token_urlsafe(48))"`. It then runs `brew bundle`, `uv sync --frozen`, `pnpm --dir $BENEFIT_FE_DIR install --frozen-lockfile` and `make mongo-up`.
  - Run `make setup` on this branch and confirm the replica set is up and the `benefit_owner` and `benefit_app` users exist before the next two tasks.
- [X] T040 Implement the integration test harness `benefit-be/tests/integration/conftest.py` (FR-000-17, FR-000-20). A session fixture refuses unless `APP_ENV=test` and `LLM_MODE=fake`, then resets MongoDB before the run: for now `python -m db.migrate down base` then `up head`, and the US1 reset task switches it to `python -m db.seeds.reset`. It provides fixtures for the `benefit_app` and `benefit_owner` clients and the Temporal client. Reuse it from `tests/db/` and `tests/api/` through `pytest_plugins` in `tests/conftest.py`. [PUI]
- [X] T041 Write `benefit-be/tests/db/test_migrations.py`, marked `integration` [KD]:
  - `test_baseline_upgrade_downgrade_upgrade_round_trip`: up, down to base (no collections left except `_migrations`), up again.
  - `test_migration_runner_records_and_skips_applied_versions`.
### Makefile skeleton and the OpenAPI → client pipeline

- [X] T042 Create `benefit-be/Makefile` with the check targets only (the run targets come in US1): `lint`, `typecheck`, `test-unit`, `test-workflow`, `test-contract`, `test-integration`, `test-api`, `test-stack`, `test` (each `uv run pytest -m <marker> $(PYTEST_ARGS)`), `openapi`, `openapi-check`. `test` runs `-m "not live_llm and not stack and not api"` so it needs no running stack. `test-api` and `test-stack` need the stack from `make dev` or `Procfile.ci`. Follow [contracts/commands-and-ci.md](contracts/commands-and-ci.md). [PUI]
- [X] T043 Implement `benefit-be/scripts/export_openapi.py`: build `create_app()` with test settings and write `benefit-be/openapi/openapi.json` with `sort_keys=True, indent=2` plus a trailing newline. Run `make openapi` and commit the file (FR-000-26, R18). [PUI]
- [X] T044 Implement `benefit-fe/scripts/gen-api.mjs` (FE-3, R18) [PUI]:
  - Read the SHA from `benefit-fe/openapi/BE_COMMIT`.
  - Fetch `https://raw.githubusercontent.com/elinasarvari/benefit-be/<sha>/openapi/openapi.json`, or a local `../benefit-be` file when `BE_LOCAL=1`.
  - Write it to `benefit-fe/openapi/openapi.json`.
  - Run `openapi-typescript` to produce `benefit-fe/src/api/generated/schema.d.ts`.
  - Add the `api:gen` script. Install `openapi-typescript` 7.13 as a dev dependency.
- [X] T045 [P] Write the failing client test `benefit-fe/src/api/client.test.ts`: `it('parses the error envelope into ApiError with code and referenceId')`. Mock at the `src/api/` boundary. [PUI]
- [X] T046 Implement the API client layer [PUI]:
  - `benefit-fe/src/api/client.ts`: `openapi-fetch` `createClient<paths>({ baseUrl: '/api/v1', credentials: 'include' })`.
  - `benefit-fe/src/api/errors.ts`: an `ApiError` class (`status`, `code`, `message`, `fields`, `referenceId`) parsed from `ErrorEnvelope`.
  - `benefit-fe/src/api/queryClient.ts`: a `QueryClient` with the default `retry` set to `false` for 4xx.

**Checkpoint**: The contracts PR has merged and the platform core exists. User stories can start.

---
## Phase 3: User Story 1 - Run the whole system with one command (Priority: P1) 🎯 MVP

**Goal**: From a fresh clone, `make setup`, `make reset` and `make dev` (or `make prod`) start every component. `make health` shows them all healthy. `make reset` clears all data and reseeds while the system is running.

**Covers**: FR-000-01, FR-000-02, FR-000-09 (basic), FR-000-14, FR-000-27 (workflows).

**Independent Test**: On a clean Mac, follow `benefit-be/README.md`, then run [quickstart.md](quickstart.md) §1 and §2. `make health` exits 0 with every component `ready`, and after `make reset` the seeded counts and synthetic markers are back.

### Tests for User Story 1 (write first; they must fail) ⚠️

- [X] T047 [P] [US1] Write `benefit-be/tests/packages/platform/test_synthetic.py` (FR-000-14) [PUI]:
  - `test_FR_000_14_pdf_stamp_is_visible_and_detected`
  - `test_FR_000_14_image_stamp_is_visible_and_detected` (PNG and JPEG)
  - `test_FR_000_14_text_stamp_is_visible_and_detected` (plain text and HTML)
  - `test_FR_000_14_stamp_does_not_cover_body`: the label is only in the top and bottom margin bands; the body region's pixels and text are unchanged.
- [X] T048 [P] [US1] Write `benefit-be/tests/db/test_markers.py::test_FR_000_14_each_store_has_synthetic_marker`, marked `integration`. After a reset, check:
  - Mongo has `_meta` `{_id:"dataset", synthetic:true}`, and inserting `synthetic:false` is rejected by the validator.
  - DuckDB has `meta.dataset_metadata` with one row where `synthetic = true`.

  [KD]
- [X] T049 [P] [US1] Write the reset tests in `benefit-be/tests/db/seeds/test_reset.py`, marked `integration` [KD]:
  - `test_FR_000_02_reset_restores_seeded_counts_and_markers`: add a row, reset, and expect the seeded counts again.
  - `test_FR_000_02_reset_refuses_non_local_host`: guard refuses when the database host isn't localhost.
  - `test_FR_000_02_reset_refuses_unmarked_non_empty_database`.
- [X] T050 [P] [US1] Write `benefit-be/tests/db/seeds/test_generated_documents.py::test_FR_000_14_every_generated_document_is_marked`, marked `integration`. After `make seed`, every file in `db/seeds/generated/` passes `is_marked()`. [KD]
- [X] T051 [P] [US1] Write the API health tests in `benefit-be/tests/apps/api/routers/test_health.py`, replacing the scaffold test [PUI]:
  - `test_FR_000_09_health_returns_ok_with_synthetic_flag`: `GET /api/v1/health` → `{component:"api", status:"ok", version, synthetic_data:true}`.
  - `test_FR_000_09_ready_returns_ready_when_all_checks_ok`: checks faked through `app.dependency_overrides`.
  - `test_FR_000_09_health_and_ready_need_no_session`.
- [X] T052 [P] [US1] Write the worker start-up tests in `benefit-be/tests/apps/worker/test_main.py` and `benefit-be/tests/apps/worker/test_health.py` [WF]:
  - `test_FR_000_04_worker_missing_setting_exits_naming_it`.
  - `test_FR_000_09_worker_ready_true_when_polling`: fake Temporal and Mongo probes.
- [X] T053 [P] [US1] Write the workflow tests (TW-13, FR-000-27) [WF]:
  - `benefit-be/tests/apps/worker/workflows/test_calendar.py::test_FR_000_27_chicago_date_across_utc_midnight`: pure unit test; 05:30 UTC is the previous Chicago day.
  - `benefit-be/tests/apps/worker/workflows/test_smoke.py::test_FR_000_27_smoke_workflow_timer_fires_and_uses_chicago_date`, marked `workflow`: `WorkflowEnvironment.start_time_skipping()`, activities stubbed (TW-15), one-day timer skipped.
- [X] T054 [P] [US1] Write `benefit-fe/src/components/SyntheticBanner.test.tsx` [PUI]:
  - `it('FR-000-14: shows the SYNTHETIC banner on every route including sign-in')`: render the router at `/`, `/sign-in` and an unknown route; expect `getByRole('region', {name: /synthetic/i})`.
  - The banner cannot be dismissed.

### Implementation for User Story 1

- [X] T055 [P] [US1] Implement `benefit-be/packages/platform/synthetic.py` (R24) [PUI]:
  - `SYNTHETIC_LABEL = "SYNTHETIC – NOT A REAL DOCUMENT"`.
  - `stamp_pdf(data) -> bytes`: a reportlab overlay with label bands in the top and bottom margins of every page, merged with pypdf; set metadata `Subject`/`Keywords` = `SYNTHETIC`.
  - `stamp_image(data) -> bytes`: a Pillow margin band; PNG `tEXt` or JPEG comment `SYNTHETIC`.
  - `stamp_text(text, *, html=False) -> str`: label first line, or `<div role="note">` for HTML.
  - `is_marked(data, media_type) -> bool`.
- [X] T056 [P] [US1] Implement the Mongo export for the reporting store, `benefit-be/analytics/export_mongo.py` (KD-15) [KD]: read `_meta` (and, for later features, pseudonymised projections of other collections) with `MONGO_URL_OWNER` and write them to DuckDB staging tables in `DUCKDB_PATH` (`staging.dataset_metadata`). It exports no personal data. Entry point: `python -m analytics.export_mongo`.
- [X] T057 [US1] Implement `benefit-be/db/seeds/generate.py` (BA-11, KD-13) [KD]:
  - Fixed `SEED` constant and uuid5 namespace.
  - Write the households for `applicant1` and `applicant2`.
  - Write a one-page sample pay stub PDF, stamped with `stamp_pdf`, to `db/seeds/generated/`.
  - Write the `_meta` document (`_id: "dataset"`, `synthetic: true`, seed, generator version, time).
  - Entry point: `python -m db.seeds.generate`.
- [X] T058 [P] [US1] Create the minimal dbt-duckdb project [KD]:
  - `benefit-be/analytics/dbt_project.yml` and `benefit-be/analytics/profiles.yml`. The DuckDB path comes from `DUCKDB_PATH`, and models read the staging tables written by the export (KD-15).
  - `benefit-be/analytics/models/meta/dataset_metadata.sql`.
  - `benefit-be/analytics/models/meta/schema.yml` with tests: exactly one row, `synthetic = true`.
- [X] T059 [US1] Implement `benefit-be/db/seeds/reset.py` (`python -m db.seeds.reset`, R13) [KD]:
  1. Guard: refuse with exit code 3 unless `APP_ENV` is `dev`, `prod` or `test`, the Mongo host is `localhost` or `127.0.0.1`, and the `_meta` marker says synthetic or the database is empty.
  2. `python -m db.migrate down base`, then `python -m db.migrate up head`.
  3. Delete `DUCKDB_PATH`.
  4. Run `db.seeds.generate`.
  5. Run `python -m analytics.export_mongo`, then `dbt build --project-dir analytics`.
  6. Switch the session fixture in `benefit-be/tests/integration/conftest.py` to call `python -m db.seeds.reset`.
- [X] T060 [P] [US1] Implement `benefit-be/packages/platform/health.py` [PUI]:
  - A `Check` protocol (`name`, `required`, `async probe() -> CheckStatus`) with a 2 s timeout per probe.
  - `MongoCheck`: pings the server and reads the `_meta` synthetic document; down if either fails or `synthetic` isn't true.
  - `HttpCheck(url, required)`, used for Phoenix.
  - `serve_health(component, port, checks)`: a tiny ASGI app with `/health` and `/ready`, run by `uvicorn.Server` in the caller's event loop.
  - No `temporalio` import (BA-7).
- [X] T061 [US1] Implement the API health endpoints [PUI]:
  - `benefit-be/apps/api/services/readiness.py`: builds the Mongo and Temporal checks. The Temporal check uses `temporalio.client.Client.connect` with `check_health()` and a 2 s timeout.
  - `benefit-be/apps/api/routers/health.py`: `GET /health` and `GET /ready`. `/ready` returns 503 only when the status is `not_ready`. Neither route requires a session.
  - `benefit-be/apps/api/schemas/health.py`.
  - Register the router in `create_app`.
- [X] T062 [P] [US1] Implement `benefit-be/apps/worker/policies.py` (TW-10, R9) [WF]:
  - `DEFAULT`: `start_to_close_timeout=30s`; retry with `initial_interval=1s`, `backoff_coefficient=2`, `maximum_interval=30s`, `maximum_attempts=5`.
  - `AGENT_STEP`: `start_to_close_timeout=120s`, `maximum_attempts=3`.
  - Both list `ValidationError`, `PermissionDenied` and `CredentialRejected` in `non_retryable_error_types`.
  - Document the retry budget: at most 3 × (1 + `LLM_MAX_RETRIES`) model calls.
- [X] T063 [P] [US1] Implement `benefit-be/apps/worker/workflows/calendar.py`: pure `chicago_date(utc_dt)` and `days_between(a, b)`. Build the `ZoneInfo("America/Chicago")` at import inside `workflow.unsafe.imports_passed_through()` (TW-1). [WF]
- [X] T064 [US1] Implement the `SmokeWorkflow` skeleton (TW-3) [WF]:
  - `benefit-be/apps/worker/workflows/smoke.py`: input `SmokeInput{case_id}`; workflow ID `case-{case_id}`; compute the Chicago date from `workflow.now()`; `workflow.sleep(timedelta(days=1))`; call the activity `smoke_step` with `policies.DEFAULT`.
  - `benefit-be/apps/worker/activities/smoke.py`: `smoke_step` logs and returns its input.
- [X] T065 [US1] Implement `benefit-be/apps/worker/health.py`: a worker `ReadinessReport` where Temporal, Mongo and `polling` are required and `tracing` is optional; polling is true once `Worker.run()` has started. Implement `benefit-be/apps/worker/main.py` (`python -m apps.worker.main`), which runs in this order: [WF]
  1. `load_settings()`.
  2. `configure_logging(settings, "worker")`.
  3. Start the health server on `WORKER_HEALTH_PORT`.
  4. Connect to Temporal with bounded backoff. Temporal being down shows as not ready, not as a crash.
  5. Build activity instances once (TW-12).
  6. Run the `Worker` on `TEMPORAL_TASK_QUEUE`.
- [X] T066 [US1] Record the history `benefit-be/tests/apps/worker/histories/smoke_v1.json` from a green time-skipping run (V6). Then write `benefit-be/tests/apps/worker/workflows/test_smoke_replay.py::test_smoke_workflow_replays_recorded_history` using `Replayer` (TW-14). [WF]
- [X] T067 [US1] Write `benefit-be/tests/apps/worker/workflows/test_smoke_restart.py::test_smoke_workflow_resumes_after_worker_restart`, marked `workflow` (TW-16): stop the worker mid-timer, start a new worker, and check the workflow completes. [WF]
- [X] T068 [P] [US1] Implement `benefit-be/scripts/check_health.py` (`make health`) [PUI]:
  - Poll the readiness endpoints of `api` (8000) and `worker` (8001), `temporal operator cluster health`, Phoenix `GET :6006/healthz`, and the `web` page `/` on 5173 (or 4173 when `APP_ENV=prod`).
  - Print a table of component and status.
  - Exit 0 only if every component is `ready` or `degraded`.
- [X] T069 [US1] Create `benefit-be/Procfile` and `benefit-be/Procfile.prod` with the process lines from [contracts/commands-and-ci.md](contracts/commands-and-ci.md) (R13) [PUI]:
  - `temporal`: `temporal server start-dev --db-filename .data/temporal.db`
  - `api`: uvicorn `--factory`; `--reload` in dev only
  - `worker`
  - `phoenix`: `uvx --from arize-phoenix==21.0.0 phoenix serve`, with its working directory under `.data/phoenix`
  - `web`: `pnpm --dir $BENEFIT_FE_DIR dev` in dev, `preview` in prod
- [X] T070 [US1] Add the remaining run targets to `benefit-be/Makefile` (`doctor` and `setup` are already in place from Phase 2): `dev`, `prod`, `seed`, `reset`, `health`, `e2e`, as specified in [contracts/commands-and-ci.md](contracts/commands-and-ci.md). [PUI]
  - `prod` builds the frontend, then runs `APP_ENV=prod honcho -f Procfile.prod start`.
- [X] T071 [US1] Extend `make reset` in `benefit-be/Makefile` (R13) [PUI]:
  - After `python -m db.seeds.reset`, run `temporal workflow terminate --namespace $TEMPORAL_NAMESPACE --query 'ExecutionStatus="Running"' --yes` and delete the schedules.
  - Then delete the Phoenix project `$TRACING_PROJECT` through its REST API. If Phoenix is unreachable, print a warning instead of failing.
  - **Verify V1** against a local `phoenix serve`. If the delete endpoint doesn't exist, use the R26 fallback (delete `.data/phoenix` only when Phoenix is stopped, and warn otherwise) and record the result under R26 in `specs/000-platform-foundations/research.md`.
- [X] T072 [P] [US1] Implement the frontend shell [PUI]:
  - `benefit-fe/src/components/SyntheticBanner.tsx`: a `<section role="region" aria-label="Synthetic data notice">` that cannot be dismissed and appears on every route (FR-006-11).
  - `benefit-fe/src/app/AppShell.tsx`: renders the banner plus `<Outlet/>`.
  - `benefit-fe/src/features/errors/NotFoundPage.tsx`.
- [X] T073 [US1] Implement `benefit-fe/src/app/router.tsx` (React Router): an `AppShell` layout, a `/sign-in` placeholder, the `/caseworker` and `/applicant` placeholder routes, and a `*` NotFound route. Update `benefit-fe/src/main.tsx` to wrap the app in `QueryClientProvider` and `RouterProvider`. [PUI]
- [X] T074 [P] [US1] Implement `benefit-fe/src/lib/time.ts`: `formatDate` and `formatDateTime` using `Intl.DateTimeFormat('en-US', {timeZone: 'America/Chicago'})`. Write `benefit-fe/src/lib/time.test.ts` with `it('FR-000-27: formats a 05:30Z instant as the previous Chicago day')` first. [PUI]
- [X] T075 [US1] Write `benefit-be/README.md` covering the path from clone to healthy system (SC-000-01): prerequisites, cloning both repos side by side, `make doctor`, `setup`, `reset`, `dev` and `health`, a ports table, `make prod`, `make reset`, and troubleshooting. Link [quickstart.md](quickstart.md). [PUI]

**Checkpoint**: US1 works on its own. [quickstart.md](quickstart.md) §1–§2 pass.

---

## Phase 4: User Story 2 - Sign in with a role (Priority: P1)

**Goal**: Seeded applicant, caseworker and supervisor accounts can sign in. A session identifies the user and their role and expires after 8 h. Every protected operation refuses a missing or expired session. Sign-in and refused access are audited. The worker mints case-scoped system credentials for agent tools.

**Covers**: FR-000-05, -06, -07, -21, -22, -23.

**Independent Test**: Run [quickstart.md](quickstart.md) §4. Signing in as each demo user returns `SessionInfo` with the right role. No cookie returns 401 `auth.required`. An expired session returns 401 `auth.session_expired`. In the SPA, each role lands in its own area and is redirected away from the others.

### Tests for User Story 2 (write first; they must fail) ⚠️

- [X] T076 [P] [US2] Write `benefit-be/tests/packages/platform/auth/test_passwords.py::test_FR_000_21_hash_is_argon2id_and_verifies`: the hash starts with `$argon2id$`, `verify_password` rejects a wrong password, and `needs_rehash` is false for a fresh hash. [PUI]
- [X] T077 [P] [US2] Write the token tests in `benefit-be/tests/packages/platform/auth/test_tokens.py`, using `FixedClock` [PUI]:
  - `test_FR_000_07_session_expires_after_configured_ttl`: default 8 h, and a configured value.
  - `test_FR_000_22_credential_names_one_case_and_has_no_user_role`.
  - `test_FR_000_22_credential_rejected_for_other_case`.
  - `test_FR_000_22_credential_rejected_after_expiry`.
  - `test_FR_000_22_user_token_rejected_by_system_verifier`.
  - `test_FR_000_22_system_token_rejected_by_user_verifier`.
- [X] T078 [P] [US2] Write the auth route tests in `benefit-be/tests/apps/api/routers/test_auth.py`, with the identity provider and audit writer faked through `dependency_overrides` [PUI]:
  - `test_FR_000_21_login_success_sets_httponly_samesite_strict_cookie`.
  - `test_FR_000_21_unknown_user_and_wrong_password_identical_401`: same body code `auth.invalid_credentials`, same message.
  - `test_FR_000_06_me_without_cookie_returns_auth_required`.
  - `test_FR_000_07_expired_session_returns_session_expired`.
  - `test_FR_000_22_system_credential_rejected_on_user_routes`.
  - `test_logout_clears_cookie_returns_204`.
  - `test_FR_000_23_sign_in_success_and_failure_audited_without_username`: the audit entries have `actor_type` `user`/`anonymous`, and no field contains the typed username.
- [X] T079 [P] [US2] Write `benefit-be/tests/apps/api/dependencies/test_authz.py`, a parametrized PL-7 role matrix on a probe route `require_roles(Role.caseworker)` [PUI]:
  - `test_FR_000_05_supervisor_allowed_where_caseworker_allowed`.
  - `test_FR_000_05_applicant_rejected_with_forbidden`.
  - `test_FR_000_23_refused_access_writes_access_refused_audit_entry`.
- [X] T080 [P] [US2] Write the audit-log tests in `benefit-be/tests/db/test_audit_log.py`, marked `integration` [KD]:
  - `test_FR_000_23_app_user_update_delete_denied_insert_and_find_allowed` (parametrized: `update_one`, `update_many`, `delete_one`, `delete_many`, `replace_one` are refused; `insert_one` and `find` work).
  - `test_FR_000_23_app_user_cannot_change_audit_log_even_through_collmod_or_drop`: the `benefit_app` client gets an authorization error (code 13) for `collMod`, `drop` and `renameCollection` as well.
  - `test_FR_000_23_audit_schema_has_no_free_text_column`: the validator has `additionalProperties: false`, no object or array field, and a length cap on every string; inserting a document with an extra field or a 1000-character string is rejected.
- [X] T081 [P] [US2] Write the household-scope tests in `benefit-be/tests/db/test_scope.py`, marked `integration` [KD]:
  - `test_FR_000_06_repository_without_scope_raises`: calling a scoped repository function with no `Scope` raises `ScopeRequired` and returns no data.
  - `test_FR_000_19_applicant_cannot_read_other_household`: an applicant `Scope` for household A reads nothing belonging to household B, and a caseworker `Scope` reads both.
  - `test_FR_000_19_system_scope_limited_to_its_case`: a system-credential `Scope` reads only its own `case_id`.
  - `test_FR_000_19_no_unscoped_queries_on_household_collections`: scan the repository modules and fail on any direct `find`, `find_one`, `aggregate`, `update_*` or `delete_*` call on a household-scoped collection outside the scoped helper.
- [X] T082 [P] [US2] Write the user-seeding tests in `benefit-be/tests/db/seeds/test_users.py`, marked `integration` [KD]:
  - `test_FR_000_05_seed_creates_each_role`: `applicant1` (household A), `applicant2` (household B), `caseworker1`, `supervisor1`.
  - `test_FR_000_21_seed_refuses_without_demo_password`.
  - `test_FR_000_21_password_stored_as_argon2id`: use `verify_password`, not hash equality.
- [X] T083 [P] [US2] Write `benefit-be/tests/apps/worker/activities/test_agent_step.py`, using `ActivityEnvironment` [WF]:
  - `test_FR_000_22_credential_expires_at_step_end`: `exp == attempt start + start_to_close_timeout`.
  - `test_FR_000_22_new_credential_per_retry_attempt`.
  - `test_FR_000_22_token_not_in_activity_result_or_logs`.
- [X] T084 [P] [US2] Write the frontend auth tests [PUI]:
  - `benefit-fe/src/features/auth/SignInPage.test.tsx`:
    - `it('FR-000-21: signs in and routes caseworker to /caseworker')`.
    - `it('FR-000-21: shows the error message and reference ID on invalid credentials')`.
  - `benefit-fe/src/app/RequireRole.test.tsx`:
    - `it('FR-000-05: redirects an applicant away from /caseworker')`.
    - `it('FR-000-05: lets a supervisor into caseworker routes')`.
  - Add to `benefit-fe/src/api/client.test.ts`: `it('FR-000-07: a 401 session_expired redirects to /sign-in?reason=expired')`.

### Implementation for User Story 2

- [X] T085 [P] [US2] Implement `benefit-be/packages/platform/auth/passwords.py`: `hash_password`, `verify_password` and `needs_rehash` with `argon2.PasswordHasher()` defaults (argon2id). Also add a module constant `DUMMY_HASH` so unknown users can be verified at constant time (R5). [PUI]
- [X] T086 [P] [US2] Implement `benefit-be/packages/platform/auth/roles.py` with `implies(role) -> set[Role]` (`supervisor ⊇ caseworker`) and `has_role(principal, *allowed)`. [PUI]
- [X] T087 [US2] Implement `benefit-be/packages/platform/auth/tokens.py` (PyJWT HS256, R4 and R6) [PUI]:
  - `issue_user_token(user, settings, clock)` sets claims `typ="user"`, `sub`, `role`, `hh` (applicants only), `iat`, `exp = iat + SESSION_TTL_HOURS*3600` and `jti`. Signed with `SESSION_SECRET`.
  - `verify_user_token(token, settings, clock) -> Principal`. Expiry raises `SessionExpired`; anything else raises `AuthRequired`; `typ != "user"` is rejected; no leeway.
  - `issue_system_credential(case_id, workflow_id, step, ttl, settings, clock)` and `verify_system_credential(token, expected_case_id, settings, clock) -> SystemCredentialClaims`. These use `SYSTEM_CREDENTIAL_SECRET` and `aud="agent-tools"`, and reject a `typ` mismatch, an expired token or a `case_id` mismatch.
- [X] T088 [P] [US2] Implement `benefit-be/packages/platform/auth/identity.py`: an `IdentityProvider` protocol with `authenticate(username, password) -> Principal | None` and `get_user(user_id) -> UserPublic | None` (constitution IX). [PUI]
- [X] T089 [P] [US2] Implement `benefit-be/packages/platform/audit.py` (R15, FR-000-23) [PUI]:
  - An `AuditWriter` protocol with `async write(entry: AuditLogEntry)`.
  - `MongoAuditWriter`, which only ever calls `insert_one` on `audit_log` with `MONGO_URL_APP`, and accepts an optional transaction session so a caller can write the entry with its own change.
  - `InMemoryAuditWriter` for tests.
- [X] T090 [US2] Implement `benefit-be/db/seeds/users.py` [KD]:
  - Seed `applicant1` (household A), `applicant2` (household B), `caseworker1` and `supervisor1`, with display names `"Applicant One"`, `"Applicant Two"`, `"Caseworker One"` and `"Supervisor One"`, and uuid5 IDs.
  - Hash `DEMO_PASSWORD` with `hash_password`. Exit non-zero if it is empty.
  - Call it from `db/seeds/generate.py`.
- [X] T091 [US2] Implement the user and scope repositories [PUI]:
  - `benefit-be/db/scope.py` (used by every repository, KD-10, R16): `Scope` built from a `Principal` or a verified `SystemCredentialClaims`, `ScopeRequired`, and a `scoped_filter(scope, collection)` helper that adds `{"household_id": ...}` for applicants and `{"case_id": ...}` for a system credential, and nothing for caseworkers and supervisors. Filters are built from typed `UUID` values only.
  - `benefit-be/apps/api/repositories/users.py`: `lookup_for_login(username)` finds one user by username (collation strength 2) with the projection `_id`, `password_hash`, `role`, `household_id`, `display_name`; `get_public(user_id)` projects the public fields only. The username is validated against `LoginRequest`'s pattern first, so no operator can reach the filter.
  - `benefit-be/apps/api/identity_local.py`: `LocalIdentityProvider`. When the user is unknown it still runs `verify_password(DUMMY_HASH, …)`.
- [X] T092 [US2] Implement `benefit-be/apps/api/dependencies/db.py`: one `AsyncMongoClient` per process from `MONGO_URL_APP` with `serverSelectionTimeoutMS` and `connectTimeoutMS` set (FR-000-13), a per-request database handle, and a `Scope` built from the `Principal` (R16). [PUI]
- [X] T093 [US2] Implement `benefit-be/apps/api/dependencies/auth.py` [PUI]:
  - `current_principal`: read the `benefit_session` cookie, call `verify_user_token`, bind `user_id` and `role` to the log context.
  - `require_roles(*roles)`: on refusal, write an `access_refused` audit entry with `target_type="route"`, `target_id` set to the route template and `reason_code="role_not_allowed"`, then raise `Forbidden`.
  - Any `typ=system` token gets `AuthRequired`.
- [X] T094 [US2] Implement the sign-in flow [PUI]:
  - `benefit-be/apps/api/services/auth_service.py`:
    - `login`: authenticate, issue the token, audit `sign_in` success (`actor_type=user`) or failure (`actor_type=anonymous`, `target_id=NULL`, `reason_code=invalid_credentials`), and never log the username.
    - `me`, `logout`.
  - `benefit-be/apps/api/routers/auth.py`:
    - `POST /auth/login` sets the cookie `HttpOnly; SameSite=Strict; Path=/api`, plus `Secure` when `APP_ENV=prod`.
    - `POST /auth/logout` returns 204 and clears the cookie.
    - `GET /auth/me`.
  - `benefit-be/apps/api/schemas/auth.py`.
  - Register the router. Follow [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml) exactly.
- [X] T095 [US2] Implement `benefit-be/apps/worker/activities/agent_step.py` (R6) [WF]:
  - `AgentStepActivities`, constructed once with `settings` and `clock`.
  - A helper `_mint(case_id, workflow_id, step)` called at the start of **each attempt** with `ttl = activity.info().start_to_close_timeout`. It passes the token straight to the callee as keyword-only `tool_credential` and never returns, logs or puts it in a result.
  - Register `AgentStepActivities` in `apps/worker/main.py`.
- [X] T096 [US2] Run `make openapi` and commit the regenerated `benefit-be/openapi/openapi.json`. Check it matches the paths and schemas in [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml). In `benefit-fe`, set `openapi/BE_COMMIT` to the new benefit-be SHA and run `pnpm api:gen` to update `benefit-fe/src/api/generated/schema.d.ts`. [PUI]
- [X] T097 [US2] Implement `benefit-fe/src/api/auth.ts` with the hooks `useMe()` (query key `['auth','me']`), `useLogin()` and `useLogout()`, both mutations invalidating `['auth','me']` (FE-4, FE-5). In `benefit-fe/src/api/queryClient.ts`, add a global 401 handler: `auth.session_expired` goes to `/sign-in?reason=expired`, `auth.required` goes to `/sign-in?reason=required`. [PUI]
- [X] T098 [US2] Implement the sign-in UI [PUI]:
  - `benefit-fe/src/app/RequireRole.tsx`: uses `useMe` and role implication, and handles loading, error and forbidden states (FE-6, FE-10).
  - `benefit-fe/src/features/auth/SignInPage.tsx`: React 19 `useActionState`, labelled inputs, an expired-session notice from `?reason=`, and `ErrorState` with the reference ID.
  - Create `benefit-fe/src/components/ErrorState.tsx`, which shows the message and the reference ID (FE-10).
  - `benefit-fe/src/features/errors/ForbiddenPage.tsx`.
  - Guard `/caseworker` with `caseworker` and `supervisor`, and `/applicant` with `applicant`, in `src/app/router.tsx`.
  - Add a sign-out button to `AppShell`.

**Checkpoint**: US1 and US2 both work on their own. [quickstart.md](quickstart.md) §4 passes.

---
## Phase 5: User Story 5 - Quality gates on every change (Priority: P1)

**Goal**: Every PR in `benefit-be` and `benefit-fe` runs static checks, unit, workflow, contract, integration and end-to-end tests with the AI faked, and shows the results on the PR. Contract drift fails and names the difference. The six demo journeys exist in the e2e suite as pending.

**Covers**: FR-000-16, -17, -18, -19, -20 (CI side), -24, -25, -26; SC-000-03, SC-000-06, SC-000-08.

**Depends on**: US1 (Procfiles, reset) and US2 (sign-in, for the e2e setup).

**Independent Test**: Run [quickstart.md](quickstart.md) §9. Open a throwaway draft PR with a lint error, a failing test and an un-regenerated route change. `static`, `unit` and `contract` fail; `contract` names the changed path; a clean run is green in under 15 minutes.

### Tests for User Story 5 (write first; they must fail) ⚠️

- [X] T099 [P] [US5] Write `benefit-be/tests/contract/test_openapi.py::test_FR_000_18_live_schema_matches_committed_and_names_diff`, marked `contract`. Compare `create_app().openapi()` with `openapi/openapi.json`. On a mismatch, the assertion message lists the added, removed and changed paths and schemas. [PUI]
- [X] T100 [P] [US5] Write `benefit-be/tests/contract/test_ci_workflow.py::test_FR_000_16_ci_runs_every_required_job`, marked `contract`. Load `.github/workflows/ci.yml` with `yaml.safe_load` (add `pyyaml` to the dev group) and assert that the jobs `static`, `unit`, `workflow`, `contract`, `integration` and `e2e` exist, that `static` runs ruff, `mypy --strict`, `pip-audit` and gitleaks, and that `e2e` sets `LLM_MODE=fake`. Add the matching `benefit-fe/src/ci/ciWorkflow.test.ts` with `it('FR-000-16: runs every required job')` for `static`, `unit`, `contract` and `e2e` (add the `yaml` package as a dev dependency). [PUI]
- [X] T101 [P] [US5] Write the FR-000-26 tests [PUI]:
  - `benefit-be/tests/contract/test_openapi.py::test_FR_000_26_committed_openapi_file_is_current_and_sorted`, marked `contract`: the committed `openapi/openapi.json` equals the regenerated one byte for byte (sorted keys, trailing newline).
  - `benefit-fe/src/api/generated.test.ts`: `it('FR-000-26: BE_COMMIT is a full commit SHA')` and `it('FR-000-26: the generated schema is current for the vendored openapi file')`, which regenerates into a temp directory and compares with `src/api/generated/schema.d.ts`.
- [X] T102 [P] [US5] Write `benefit-be/tests/contract/test_every_route_protected.py::test_FR_000_06_every_non_health_route_requires_session`, marked `contract`, parametrized over `app.routes` (SC-000-02). Every route except `/api/v1/health`, `/api/v1/ready` and `POST /api/v1/auth/login` must return 401 `auth.required` without a cookie. [PUI]
- [X] T103 [P] [US5] Write the tool-schema snapshot harness `benefit-be/tests/contract/test_tool_schemas.py::test_FR_000_18_tool_schemas_match_snapshots`, marked `contract`. It compares each MCP tool's input and output JSON Schema with `tests/contract/tool_schemas/<server>/<tool>.json`, and passes vacuously until 005 registers tools. [PUI]
- [X] T104 [P] [US5] Write the CI-script tests in `benefit-be/tests/scripts/test_resolve_sibling_ref.py`, using a local bare git repo fixture [PUI]:
  - `test_FR_000_25_uses_same_named_branch_when_present`.
  - `test_FR_000_25_falls_back_to_main`.
- [X] T105 [P] [US5] Write `benefit-be/tests/integration/test_versions.py::test_FR_000_24_store_major_versions_match_local`, marked `integration`. Check the Mongo `buildInfo.version` starts with `8.0`, the server is a replica-set member (`hello.setName == "rs0"`), and `temporal --version` matches `TEMPORAL_CLI_VERSION` in the Makefile. [KD]
- [X] T106 [P] [US5] Write the fake-model tests in `benefit-be/tests/packages/rag/test_fake_models.py` [KD]:
  - `test_FR_000_24_fake_embedder_deterministic_across_processes`: compare with a subprocess.
  - Hypothesis property: for any text the vector has 1024 dimensions and unit L2 norm (empty text gives the defined zero vector), and the same input always gives the same vector.
  - `test_FR_000_24_fake_reranker_orders_by_token_overlap`.
- [X] T107 [P] [US5] Write `benefit-be/tests/apps/worker/test_smoke_integration.py::test_FR_000_17_worker_runs_smoke_against_local_temporal`, marked `integration`. Start the real worker against the local Temporal dev server, run `SmokeWorkflow` with a time-skipped timer or a short-timer override, and assert it completes. [WF]
- [X] T108 [P] [US5] Write `benefit-be/tests/stack/test_stack_health.py::test_FR_000_01_every_component_ready`, marked `stack`. Run `scripts/check_health.py` against the running `Procfile.ci` stack and expect exit 0. CI runs it in the `e2e` job, with the `api` tests. [PUI]

### Implementation for User Story 5

- [X] T109 [P] [US5] Implement the fake and real retrieval models (FR-000-24) [KD]:
  - `benefit-be/packages/rag/embeddings.py`:
    - An `Embedder` protocol.
    - `FakeEmbedder`: sha256 token hashing into 1024 buckets with a fixed seed, L2-normalised.
    - `QwenEmbedder`: lazily imports the `ml` group; loaded once per process (KD-7).
  - `benefit-be/packages/rag/rerank.py`: a `Reranker` protocol, `FakeReranker` (token overlap) and `BgeReranker` (lazy).
  - `benefit-be/packages/rag/factory.py`: `get_embedder(settings)` and `get_reranker(settings)`, chosen by `EMBEDDER` and `RERANKER`.
- [X] T110 [P] [US5] Add the secrets and pre-commit setup (PL-14, SC-000-03) [PUI]:
  - `benefit-be/.pre-commit-config.yaml`: ruff check and format, mypy, gitleaks; pinned revs.
  - `benefit-be/.gitleaks.toml`: default rules plus an allowlist for `.env.example` placeholders.
  - Add `check` to `benefit-be/Makefile`: `lint typecheck test-unit test-workflow test-contract openapi-check`, then `gitleaks detect --no-banner` and `uv run pip-audit`.
- [X] T111 [P] [US5] Implement `benefit-be/scripts/ci/resolve-sibling-ref.sh <sibling-repo-url>` (R19) and copy it to `benefit-fe/scripts/ci/resolve-sibling-ref.sh` [PUI]:
  - `BRANCH=${GITHUB_HEAD_REF:-$GITHUB_REF_NAME}`.
  - If `git ls-remote --exit-code --heads <url> "refs/heads/$BRANCH"` succeeds, print that branch; otherwise print `main`.
  - Append `Sibling ref: <ref>` to `$GITHUB_STEP_SUMMARY`.
- [X] T112 [P] [US5] Create `benefit-be/Procfile.ci`: `temporal`, `api` (no reload), `worker` and `web` (`pnpm --dir $BENEFIT_FE_DIR preview`), with **no** phoenix. Create `benefit-be/scripts/ci/wait-ready.sh`, which polls `make health` with a 180 s timeout. [PUI]
- [X] T113 [US5] Create `benefit-be/.github/workflows/ci.yml` (R19, R25, [contracts/commands-and-ci.md](contracts/commands-and-ci.md)) [PUI]:
  - Triggers: `pull_request`, and `push` to `main`. Use `concurrency` with cancel-in-progress. Pin actions by SHA.
  - Cache uv, pnpm, Playwright browsers and the Temporal CLI.
  - Job-level env: `APP_ENV=test`, `LLM_MODE=fake`, `EMBEDDER=fake`, `RERANKER=fake`, `TRACING_ENABLED=false`, and `DEMO_PASSWORD` from `openssl rand`.
  - Parallel jobs:
    - `static` (8 min)
    - `unit` (8 min)
    - `workflow` (8 min)
    - `contract` (8 min)
    - `integration` (8 min): install MongoDB 8.0 from MongoDB's apt repository (the `mongodb-org` packages) and run `make mongo-up`; install the Temporal CLI at `TEMPORAL_CLI_VERSION` and run `temporal server start-dev` in the background; then `make reset` and `pytest -m integration`. The API is not running in this job, so `api` tests do not run here.
    - `e2e` (12 min):
      1. Check out benefit-fe at `resolve-sibling-ref.sh`.
      2. `pnpm install --frozen-lockfile` and `pnpm build`.
      3. Start the same service containers, plus `honcho -f Procfile.ci start &`.
      4. `wait-ready.sh`, then `pytest -m "stack or api"` against the running stack.
      5. `pnpm --dir ../benefit-fe e2e`.
      6. Upload the Playwright HTML report and traces as artifacts.
- [X] T114 [P] [US5] Create `benefit-be/.github/workflows/nightly.yml`: on schedule and `workflow_dispatch`, run the e2e job with `e2e:all` (Firefox and WebKit) against `main`. [PUI]
- [X] T115 [P] [US5] Implement `benefit-fe/scripts/check-api.mjs` and the `api:check` script: run `api:gen`, then `git diff --exit-code openapi/ src/api/generated/`. On failure, print which side is out of date (FR-000-26). [PUI]
- [X] T116 [US5] Create the Playwright harness in `benefit-fe/e2e/` (`quality-testing-playwright.md`) [PUI]:
  - `benefit-fe/e2e/playwright.config.ts`: `baseURL` from `E2E_BASE_URL`, `timezoneId: 'America/Chicago'`, `fullyParallel: true`, `workers: 2`, `retries: process.env.CI ? 2 : 0`, `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`, a setup project, and a Chromium project (plus Firefox and WebKit under `e2e:all`).
  - `benefit-fe/e2e/auth.setup.ts`: sign in per role through `POST /api/v1/auth/login` with `E2E_*_USERNAME` and `E2E_PASSWORD`, and save `e2e/.auth/<role>.json`.
  - `benefit-fe/e2e/fixtures.ts`: an axe fixture that fails on serious or critical WCAG 2.1 AA violations.
  - `benefit-fe/e2e/pages/SignInPage.ts` (Page Object Model).
  - Install `@playwright/test` 1.65 and `@axe-core/playwright`. Add the `e2e` and `e2e:all` scripts.
- [X] T117 [US5] Write `benefit-fe/e2e/sign-in.spec.ts` [PUI]:
  - `test('FR-000-06: unauthenticated visitor is redirected to sign-in')`
  - `test('FR-000-05: each role lands in its own area')`
  - `test('FR-000-14: synthetic banner visible on every page')`
  - An axe check on the sign-in page and on each landing page.
- [X] T118 [P] [US5] Create the six pending journey specs (FR-000-19, R20). Each wraps its single test in `test.fixme(...)` and carries the annotation `{ type: 'pending', description: '<FR ids>; built by <feature>' }`, following the table in [contracts/commands-and-ci.md](contracts/commands-and-ci.md): [PUI]
  - `benefit-fe/e2e/mismatch-request-info.spec.ts`
  - `benefit-fe/e2e/restart-resume.spec.ts`
  - `benefit-fe/e2e/missed-deadline-override.spec.ts`
  - `benefit-fe/e2e/automatic-renewal.spec.ts`
  - `benefit-fe/e2e/renewal-one-document.spec.ts`
  - `benefit-fe/e2e/applicant-blocked-other-household.spec.ts`
- [X] T119 [US5] Create `benefit-fe/.github/workflows/ci.yml` (R19, R25) [PUI]:
  - `static`: ESLint, `prettier --check`, `tsc --noEmit`, `pnpm audit --audit-level high`, gitleaks.
  - `unit`: Vitest.
  - `contract`: `api:check`, plus `diff openapi/openapi.json` against benefit-be's `openapi/openapi.json` at the ref from `resolve-sibling-ref.sh`.
  - `e2e`: check out benefit-be at the sibling ref, then use the same service containers, Temporal CLI, `make reset`, `Procfile.ci` and Playwright steps as in benefit-be.
  - Use the same caching, pinned actions, concurrency and `timeout-minutes` as the benefit-be workflow. Also create `benefit-fe/.github/workflows/nightly.yml` for all browsers.
- [X] T120 [US5] Validate the gates on a throwaway draft PR in `benefit-be` (quickstart §9). It should contain a ruff error, a failing unit test and a route change without `make openapi`. Confirm `static`, `unit` and `contract` fail, and that `contract` names the path. Then close it. Record the green-run duration, and if it exceeds 15 minutes, apply the R25 `@smoke` fallback. Note the result in `specs/000-platform-foundations/handoff.md`. [PUI]

**Checkpoint**: Every P1 story is done. All CI gates run on both repos.

---

## Phase 6: User Story 3 - Consistent errors, health and logs (Priority: P2)

**Goal**: Unexpected failures give clients a generic error with a reference ID that matches one log line holding the details. Logs mask personal data and carry request, case and workflow IDs across API → Temporal → activities. Readiness reports dependencies that are down. Every outbound call has a timeout and a bounded retry.

**Covers**: FR-000-08 (500 path), -09 (edge cases), -10 (propagation), -11, -13; SC-000-05.

**Independent Test**: Run [quickstart.md](quickstart.md) §5 and §7. A 422 and a forced 500 return the envelope with a reference ID, and searching the logs for it finds the stack trace. With Mongo stopped, `/health` is 200 and `/ready` is 503 with `mongo: down`.

### Tests for User Story 3 (write first; they must fail) ⚠️

- [X] T121 [P] [US3] Write `benefit-be/tests/packages/platform/test_logging.py::test_FR_000_11_personal_data_masked`, parametrized over every masked key and every pattern in [contracts/logging.md](contracts/logging.md), at nested depths and inside exception text. Plant synthetic values and assert that none of them appear in the rendered JSON line. [PUI]
- [X] T122 [P] [US3] Add `test_FR_000_08_unexpected_error_returns_generic_message_with_reference` to `benefit-be/tests/apps/api/test_errors.py`. Make a probe route raise `RuntimeError("SELECT secret FROM x")`. Expect a 500 with `internal_error` and the generic message, with no stack trace, SQL or hostname. Exactly one captured log line has the same `request_id` and contains the exception. [PUI]
- [X] T123 [P] [US3] Write the readiness tests in `benefit-be/tests/integration/test_readiness.py`, marked `integration` [PUI]:
  - `test_FR_000_09_mongo_down_not_ready_health_ok`: point `MONGO_URL_APP` at an unused port.
  - `test_FR_000_09_mongo_down_not_ready`.
  - `test_FR_000_09_ready_response_has_no_connection_details`.
- [X] T124 [P] [US3] Add `test_FR_000_09_worker_ready_false_health_true_when_temporal_down` to `benefit-be/tests/apps/worker/test_health.py`. [WF]
- [X] T125 [P] [US3] Write the resilience tests in `benefit-be/tests/packages/platform/test_resilience.py`, using an injected fake sleep [PUI]:
  - `test_FR_000_13_call_times_out`.
  - `test_FR_000_13_retries_bounded_with_exponential_backoff`.
  - `test_FR_000_13_non_retryable_error_not_retried`.
  - `test_FR_000_13_http_client_has_timeout_and_tls_verify`.
- [X] T126 [P] [US3] Write `benefit-be/tests/apps/worker/test_policies.py`, with `test_FR_000_13_validation_error_not_retried` marked `workflow` because it needs the time-skipping environment [WF]:
  - `test_FR_000_13_every_activity_call_uses_policy_preset`: an AST scan of `apps/worker/workflows/**` for `execute_activity*` calls without `**policies.<PRESET>`.
  - `test_FR_000_13_validation_error_not_retried`: time-skipping environment.
- [X] T127 [P] [US3] Write `benefit-be/tests/apps/worker/test_interceptors.py` [WF]:
  - `test_FR_000_10_activity_log_includes_case_and_workflow_id`.
  - `test_FR_000_10_request_id_header_propagated_from_client_to_activity_logs`: start with the API's client interceptor and assert the activity log has the same `request_id`.
- [X] T128 [P] [US3] Write `benefit-be/tests/api/test_errors_api.py`, marked `api` (pytest-playwright `APIRequestContext` against the running API, so it runs in the CI `e2e` job and locally with `make test-api` after `make dev`; it depends on `/auth/login` and `/auth/me` from US2) [PUI]:
  - `test_FR_000_08_login_validation_error_shape_matches_openapi`
  - `test_FR_000_08_error_responses_leak_no_internals`
  - `test_FR_000_06_me_unauthenticated_401_shape`
- [X] T129 [P] [US3] Write `benefit-fe/src/components/ErrorState.test.tsx`: `it('FR-000-08: shows the message and the reference ID, never raw details')`. [PUI]

### Implementation for User Story 3

- [X] T130 [US3] Implement the `mask_pii` structlog processor in `benefit-be/packages/platform/logging.py` (R10): key deny-list masking at any depth and the three regex patterns from [contracts/logging.md](contracts/logging.md), with values replaced by `"***"`. Run it last before rendering, on stdlib, uvicorn and temporalio records too. [PUI]
- [X] T131 [US3] Add a catch-all `Exception` handler to `benefit-be/apps/api/errors.py`. It logs `error.unhandled` with `exc_info` (masked) under the current `request_id`, and returns a 500 `ErrorEnvelope` with code `internal_error` and the fixed message "Something went wrong." Add a 503 `dependency_unavailable` mapping for `DependencyUnavailable`. [PUI]
- [X] T132 [P] [US3] Implement `benefit-be/packages/platform/resilience.py` (R9) [PUI]:
  - `call_with_retry(fn, *, timeout_s, max_attempts=settings.HTTP_MAX_ATTEMPTS, retry_on=(httpx.TransportError, TimeoutError), sleep=asyncio.sleep)`, with exponential backoff and jitter.
  - `http_client(settings)`: an `httpx.AsyncClient` with `timeout=HTTP_TIMEOUT_SECONDS` and `verify=True`.
- [X] T133 [US3] Implement `benefit-be/apps/api/temporal_client.py`: `get_temporal_client(settings)`, cached and with a connect timeout, plus a client outbound interceptor that writes header `x-request-id` from the log context on workflow start, signal and query. Use it in `services/readiness.py`. [PUI]
- [X] T134 [US3] Implement `benefit-be/apps/worker/interceptors.py`: an activity inbound interceptor that binds `workflow_id`, `run_id`, `activity_type`, `attempt`, `case_id` (from the input model or the `case-` workflow ID prefix) and `request_id` (from header `x-request-id`), and clears them on exit (TW-17). Register it in `apps/worker/main.py`. [WF]
- [X] T135 [US3] Harden readiness in `benefit-be/packages/platform/health.py` and `benefit-be/apps/worker/health.py`: a 2 s timeout per probe; a down probe reports `down` and never raises; report bodies carry only check names and statuses, with no hosts or DSNs. [PUI]

**Checkpoint**: US3 works on its own. [quickstart.md](quickstart.md) §5 and §7 pass.

---

## Phase 7: User Story 4 - Switch AI provider by configuration (Priority: P2)

**Goal**: The same code runs on the Anthropic API or Amazon Bedrock by changing `LLM_PROVIDER` alone. An unknown value refuses to start. Tests and CI never call a live model. Every AI run is traced to Phoenix, tagged by case and workflow, with personal data masked.

**Covers**: FR-000-12, -13 (model calls), -20, -28; SC-000-04, SC-000-09.

**Independent Test**: Run [quickstart.md](quickstart.md) §6 and §8. `make smoke-ai` passes with `LLM_PROVIDER=anthropic` and with `bedrock`, with no code change. `LLM_PROVIDER=openai` exits 2 naming the allowed values. The FR-000-28 tracing tests pass.

### Tests for User Story 4 (write first; they must fail) ⚠️

- [X] T136 [P] [US4] Write the factory tests in `benefit-be/tests/packages/agents/llm/test_factory.py` [AG]:
  - `test_FR_000_12_anthropic_provider_builds_chat_anthropic`.
  - `test_FR_000_12_bedrock_provider_builds_chat_bedrock_converse`.
  - `test_FR_000_12_model_id_read_from_selected_provider_setting`.
  - `test_FR_000_12_provider_sdk_imported_only_in_factory`: an AST scan of `packages/`, `apps/` and `scripts/`.
  - `test_FR_000_13_anthropic_client_has_timeout_and_bounded_retries`.
  - `test_FR_000_13_bedrock_client_has_timeout_and_bounded_retries`.
  - `test_chat_model_created_once_per_process`.
  - `test_chat_model_sets_no_temperature_or_top_p`.
- [X] T137 [P] [US4] Write the fake-model tests in `benefit-be/tests/packages/agents/llm/test_fake.py` [AG]:
  - `test_FR_000_20_fake_mode_returns_structured_output_without_network`: block sockets with a fixture.
  - `test_FR_000_20_missing_recorded_response_fails_with_clear_message`.
  - `test_FR_000_20_live_model_refused_in_tests`: with `CI=true` and `LLM_MODE=live`, building the model raises.
- [X] T138 [P] [US4] Write the tracing tests in `benefit-be/tests/packages/agents/test_tracing.py`, using `InMemorySpanExporter` behind `MaskingSpanExporter`, a fake model and a fake tool [AG]:
  - `test_FR_000_28_spans_tagged_with_case_and_workflow_id`.
  - `test_FR_000_28_span_records_model_provider_tokens_and_cost`.
  - `test_FR_000_28_exported_spans_contain_no_personal_data`: plant a synthetic name, date of birth, SSN-like value and document text.
  - `test_FR_000_28_exporter_down_agent_run_succeeds`.
  - `test_FR_000_28_tracing_disabled_installs_no_exporter`.
- [X] T139 [P] [US4] Add `test_FR_000_28_tracing_down_reports_degraded` to `benefit-be/tests/integration/test_readiness.py`, marked `integration`: with Phoenix unreachable, API `/ready` returns 200 `degraded` with `tracing: degraded`. [PUI]
- [X] T140 [P] [US4] Write `benefit-be/tests/packages/agents/llm/test_live_smoke.py`, marked `live_llm` (SC-000-04). On the configured provider, check:
  - a plain call returns
  - a cited Pydantic structured output parses
  - a field is extracted from a one-page stamped synthetic PDF
  - a tool binds with `tool_choice="auto"`
  - `AgentRunUsage` has tokens and cost

  [AG]

### Implementation for User Story 4

- [X] T141 [US4] Implement `benefit-be/packages/agents/llm/factory.py`, the **only** module that imports `langchain_anthropic`, `langchain_aws`, `anthropic` or `boto3` (AG-5, R8) [AG]:
  - `build_chat_model(settings)`:
    - `live` + `anthropic` → `ChatAnthropic(model=ANTHROPIC_MODEL_ID, timeout=LLM_TIMEOUT_SECONDS, max_retries=LLM_MAX_RETRIES, max_tokens=LLM_MAX_TOKENS)`
    - `live` + `bedrock` → `ChatBedrockConverse(model=BEDROCK_MODEL_ID, region_name=AWS_REGION, config=botocore.config.Config(connect_timeout, read_timeout, retries={"max_attempts":…, "mode":"standard"}))`
    - `recorded` or `fake` → `ReplayChatModel`
    - no `temperature` or `top_p` in any case
  - `get_chat_model()`: an `lru_cache` singleton (AG-9) that starts tracing lazily.
  - `structured(schema)`: native JSON-schema output that never forces `tool_choice` (AG-6).
  - Refuse `LLM_MODE=live` when `CI=true`.
- [X] T142 [P] [US4] Implement `benefit-be/packages/agents/llm/fake.py`: `ReplayChatModel(BaseChatModel)`. It reads JSON fixtures from `LLM_RECORDINGS_DIR`, keyed by `(prompt_id, prompt_version, sha256(input))`, and supports `bind_tools` and structured output. A missing entry raises `RecordedResponseMissing`, naming the key and the directory. Add the starter fixtures in `benefit-be/tests/fixtures/llm/`. [AG]
- [X] T143 [P] [US4] Implement `benefit-be/packages/agents/llm/pricing.py`: `cost_usd(usage_metadata, settings)` from `LLM_PRICE_INPUT_PER_MTOK` and `LLM_PRICE_OUTPUT_PER_MTOK`, and `to_usage(...) -> AgentRunUsage`. [AG]
- [X] T144 [US4] Implement `benefit-be/packages/agents/tracing.py` (R17, AG-15) [AG]:
  - `setup_tracing(settings)`: a no-op when `TRACING_ENABLED=false`. Otherwise it sets up OpenInference `LangChainInstrumentor` with the `TraceConfig` hide flags, an OTLP HTTP exporter to `TRACING_OTLP_ENDPOINT` for project `TRACING_PROJECT`, and a `BatchSpanProcessor` with a bounded queue and a 2 s export timeout.
  - `MaskingSpanExporter`: deny by default, keeping only the attributes listed under "Trace span" in [data-model.md](data-model.md).
  - `agent_run_context(case_id, workflow_id, agent, prompt_version)`, built on `using_attributes(session_id=case_id, metadata=...)`.
- [X] T145 [US4] Add the optional `tracing` check: an `HttpCheck` to Phoenix `/healthz` with `required=False` and a 1 s timeout. Add it in `benefit-be/apps/api/services/readiness.py` and `benefit-be/apps/worker/health.py`, and skip it when `TRACING_ENABLED=false`. [PUI]
- [X] T146 [US4] Add `make smoke-ai` to `benefit-be/Makefile`: `LLM_MODE=live uv run pytest -m live_llm tests/packages/agents/llm/test_live_smoke.py`. In the README, explain that the `bedrock` run needs `AWS_REGION`, `BEDROCK_MODEL_ID` (input P1) and AWS credentials. [PUI]
- [ ] T147 [US4] **Verify V4**: run `make smoke-ai` with `LLM_PROVIDER=anthropic`, and with `bedrock` once P1 is available. If native structured output fails on either provider, switch `structured()` to `bind_tools(tool_choice="auto")` plus `PydanticToolsParser`. Record the result under R26 in `specs/000-platform-foundations/research.md`. [AG]

**Checkpoint**: Every user story works on its own.

---

## Phase 8: Polish & cross-cutting concerns

- [X] T148 [P] Update `benefit-be/README.md` and `benefit-fe/README.md` with every command, the CI jobs, the provider switch, tracing and reset. Link the metarepo `specs/000-platform-foundations/quickstart.md`. [PUI]
- [X] T149 Run `make check`, `make test-integration` and `make e2e` in `benefit-be`, and `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm api:check` in `benefit-fe`. Fix anything that fails. [PUI]
- [ ] T150 Run the whole of [quickstart.md](quickstart.md) §1–§10 on a clean Mac account, and time §1 against SC-000-01 (under 30 min). Search the Phoenix traces for planted synthetic personal data for SC-000-09, and check a client error against its log line for SC-000-05 (under 1 min). [PUI]
- [X] T151 Run the `review-changes` skill on both branches: backend and frontend reviewers plus all four lane agents. Fix every rule violation it reports. [PUI]
- [X] T152 Write `specs/000-platform-foundations/handoff.md` from the template in `specs/README.md`, and tick the completed tasks in this file. List the open people inputs P1–P4 from [plan.md](plan.md). [PUI]
- [X] T153 Open the linked PRs in `benefit-be` and `benefit-fe` with the `create-pr` skill. Each PR lists every `FR-000-xx` it covers and the OpenAPI change (PL-3). [PUI]

---

## Dependencies & execution order

### Phase dependencies

- **Setup (Phase 1)**: No dependencies. T001 comes first.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks every story.** It includes `make setup` and the integration harness, so its database tests can run (they need MongoDB from `make mongo-up`). The `packages/domain` and `0001_baseline` tasks go out as the Day 1 contracts PR (R23, input P4).
- **US1 (Phase 3)**: Depends on Foundational.
- **US2 (Phase 4)**: Depends on Foundational. It reuses the US1 seed generator and router shell, so start it once the US1 seed and router tasks are merged.
- **US5 (Phase 5)**: Depends on US1 (Procfiles, reset, health) and US2 (sign-in for `auth.setup.ts`). The fake-model, version and sibling-ref tasks can start right after Foundational.
- **US3 (Phase 6)**: Depends on Foundational and US1. Its `api` tests need `/auth/login` and `/auth/me`, so run those after US2. Its other tasks are independent of US2, US4 and US5.
- **US4 (Phase 7)**: Depends on Foundational (settings). The readiness tracing check needs the US1 readiness code.
- **Polish (Phase 8)**: After every story.

### Story dependency graph

```text
Setup → Foundational ─┬─> US1 ─┬─> US2 ─┐
                      │        └────────┼─> US5 ─┐
                      ├─> US3 (after US1 health)  ├─> Polish
                      └─> US4 (after US1 health) ─┘
```

### Within each story

- Test tasks come first and must fail (constitution V).
- Domain models, then platform helpers, then repositories and services, then routers and UI.
- Commits stay split by lane tag (BA ownership).

### Ordering constraints from research

- V6: the replay test task comes after the green time-skipping smoke test.
- V1, V2, V3 and V5 run before the tasks that depend on them (reset, setup, lint, CI).
- 009 (FR-009-02, input P2) must turn on branch protection before the first feature PR merges.

---

## Parallel examples

### Phase 2 (after Setup)

```text
Task: "Create packages/domain/auth.py"
Task: "Create packages/domain/audit.py"
Task: "Create packages/domain/errors.py"
Task: "Create packages/domain/health.py"
Task: "Write tests/packages/platform/test_settings.py"
Task: "Write tests/packages/platform/test_clock.py"
Task: "Implement db/mongo/provision.py"
```

### User Story 1

```text
Task: "Write tests/packages/platform/test_synthetic.py"        [PUI]
Task: "Write tests/db/seeds/test_reset.py"                     [KD]
Task: "Write tests/apps/worker/workflows/test_smoke.py"        [WF]
Task: "Write src/components/SyntheticBanner.test.tsx"          [PUI]
# then
Task: "Implement packages/platform/synthetic.py"
Task: "Implement db/mongo/bootstrap.py"
Task: "Implement apps/worker/policies.py"
Task: "Implement apps/worker/workflows/calendar.py"
```

### User Story 2

```text
Task: "Write tests/packages/platform/auth/test_passwords.py"
Task: "Write tests/packages/platform/auth/test_tokens.py"
Task: "Write tests/db/test_audit_log.py"
Task: "Write tests/apps/worker/activities/test_agent_step.py"
# then
Task: "Implement packages/platform/auth/passwords.py"
Task: "Implement packages/platform/auth/roles.py"
Task: "Implement packages/platform/auth/identity.py"
Task: "Implement packages/platform/audit.py"
```

### User Story 5

```text
Task: "Write tests/contract/test_openapi.py"
Task: "Write tests/contract/test_every_route_protected.py"
Task: "Write tests/packages/rag/test_fake_models.py"
Task: "Create six pending journey specs in benefit-fe/e2e/"
```

### User Stories 3 and 4 (different lanes, run together)

```text
Task: "Write tests/packages/platform/test_logging.py::test_FR_000_11_..."   [PUI]
Task: "Write tests/packages/agents/llm/test_factory.py"                     [AG]
Task: "Write tests/apps/worker/test_interceptors.py"                       [WF]
```

---

## Implementation strategy

### MVP first (User Story 1)

1. Phase 1 Setup, then Phase 2 Foundational. Merge the contracts PR.
2. Phase 3 (US1): the system starts with one command and reports healthy, and reset works.
3. **Stop and validate** with [quickstart.md](quickstart.md) §1–§2. Every other lane can now run the stack locally.

### Incremental delivery (Day 1 afternoon to Day 2)

1. US2 (sign-in): other features get roles and sessions.
2. US5 (CI gates): turn them on before the first feature PR, together with 009's branch protection.
3. US3 and US4 in parallel across lanes: Platform & UI and Workflows take US3, Agents takes US4.

### Seat rotation (`specs/README.md`)

| Seat | Phases |
|---|---|
| Platform & UI | Setup, Foundational platform core, US1 (API and frontend parts), US2 (API and frontend), US5, US3 |
| Workflows + Agents | US1 and US2 worker tasks, US3 worker interceptors and policies, US4 |
| Knowledge & data | Foundational baseline, US1 seeds, reset and dbt, US2 seeds, audit-log and household-scope tests, US5 fake models |

---

## Notes

- `[P]` tasks touch different files and have no unfinished dependencies.
- The `[USn]` labels match the user stories in [spec.md](spec.md).
- Verify each test fails before implementing (red), then make it pass (green), then refactor.
- Commit after each task or logical group, split by lane tag. Never push to `main`.
- People inputs P1–P4 are tracked in [plan.md](plan.md) and don't block any task except the Bedrock half of V4.
