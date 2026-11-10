# Research: Platform Foundations (000)

Phase 0 output of `/speckit-plan`. Each entry gives the decision, the reason, and the alternatives that were considered. The inputs were the four lane plan sections (Platform & UI, Workflows, Knowledge & data, Agents), `project-rules/`, the constitution (v1.4.1), and checks against PyPI, npm and GitHub on 2026-11-09.

Versions were checked on 2026-11-09. They are pinned exactly in `pyproject.toml`/`uv.lock` and `package.json`/`pnpm-lock.yaml` when the work is done (PR-4).

---

## R1. Scaffold mismatches with the rules

**Problem.** The `benefit-be` scaffold does not follow the rules:

- Code is in `app/` with `routers/services/repositories`. BA-1 requires `apps/api/`.
- Dependencies are `>=` ranges in `requirements.txt`. PR-4 requires `uv.lock`.
- `/health` is at the root. PL-1 requires `/api/v1`.
- There is no mypy, Makefile, Procfile or CI.

The `benefit-fe` scaffold has its own gaps:

- It uses npm (`package-lock.json`). FE-1 requires pnpm.
- It uses oxlint. FE-11 requires ESLint and Prettier.
- The tsconfig does not set `strict`.
- TypeScript is `~7.0.2`.

**Decision.** Fix these in the first commits of `feature/000-platform-foundations`.

In `benefit-be`:

- `git mv app apps/api`.
- Delete `requirements.txt`. Pin every dependency in `pyproject.toml` with uv and commit `uv.lock`.
- Move `tests/test_health.py` to `tests/apps/api/routers/test_health.py` and rename it after FR-000-09.

In `benefit-fe`:

- Switch to pnpm and commit `pnpm-lock.yaml`. Delete `package-lock.json`. Add `packageManager` and an `.npmrc` with `save-exact=true`.
- Replace oxlint with ESLint (flat config, typescript-eslint, react-hooks, jsx-a11y) plus Prettier.
- Turn on `strict`, `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`.

**Rationale.** The rule files are what reviewers check against. The scaffold is one commit old, so moving it now costs almost nothing.

**Alternatives.**

- Keep the scaffold layout and amend the rules. Rejected: it would change the BA-* layout that every other lane's plan is written against.
- Keep oxlint alongside ESLint. Rejected: two linters for no stated benefit (constitution X).

## R2. Python version

**Decision.** Python **3.12**, pinned in `.python-version` and `pyproject.toml` (`requires-python = ">=3.12,<3.13"`). It comes from Homebrew `python@3.12` locally and `actions/setup-python` in CI.

**Rationale.** The constitution allows 3.11+. Two tracing dependencies set the upper bound:

- `openinference-instrumentation-langchain` 0.1.82 requires `<3.15`.
- `arize-phoenix` 21.0.0 requires `<3.16`.

`pydantic-settings` and `pymongo` need at least 3.11. Homebrew `python@3.12` (3.12.13) is already installed on the team's Macs, and the backend reviewer agent assumes 3.12.

**Alternatives.**

- 3.14: blocked by the OpenInference bound.
- 3.11: works, but gains nothing over 3.12.

## R3. Frontend toolchain versions

**Decision.**

- Node **24 LTS**, pinned in `.nvmrc` and `engines`.
- pnpm **11**.
- TypeScript **5.9.3**, which replaces the scaffold's 7.0.2.
- React Router (`react-router` 8) for routing.
- TanStack Query 5.
- Tailwind 4 and shadcn/ui.
- Vitest 5 with Testing Library.
- `@playwright/test` 1.65 with `@axe-core/playwright`.
- `openapi-typescript` 7.13 with `openapi-fetch`.

**Rationale.** `typescript-eslint` 8.72 supports TypeScript `>=4.8.4 <6.1.0`, and `openapi-typescript` 7.13 needs TypeScript `^5.x`. TypeScript 7 would break the FE-11 lint gate and the FE-3 client generator. React Router is the simplest well-known router for a Vite SPA, and FE-6 only needs role guards.

**Alternatives.**

- TypeScript 6.0.3: openapi-typescript does not support it.
- TanStack Router: typed routes are nice, but it adds a second TanStack mental model for no requirement.
- `@hey-api/openapi-ts`: FE-3 names `openapi-typescript`.

## R4. Session transport and token format

**Decision.**

- The session is a **PyJWT HS256 JWT** (PL-5), sent in an **`HttpOnly`, `SameSite=Strict`, `Path=/api` cookie, `Secure` when `APP_ENV=prod` and `WEB_ORIGIN` is https** named `benefit_session`.
- The API and SPA share one origin through the Vite dev and preview proxy (`/api` → `http://localhost:8000`).
- Claims: `typ="user"`, `sub` (user id), `role`, `hh` (household id, applicants only), `iat`, `exp`, `jti`.
- `exp` is `iat + SESSION_TTL_HOURS` (default 8; FR-000-07).
- Logout clears the cookie. There is no server-side revocation list.
- An expired token returns `401 auth.session_expired`, and the SPA sends the user to `/sign-in?reason=expired` (US2 scenario 3).

**Rationale.**

- The browser's JavaScript never sees the token.
- `SameSite=Strict` on the same origin removes the CSRF risk without a CSRF-token mechanism.
- FE-6 role guards read the role from `GET /api/v1/auth/me`.
- The spec has no logout or revocation requirement, so a denylist would be scope creep (constitution X).

**Alternatives.**

- Bearer token in `localStorage`: the token is readable by XSS. Rejected.
- Server-side session table: more state and no requirement for it.
- `revoked_sessions` table: deferred until a requirement asks for revocation.

## R5. Password hashing and identity provider

**Decision.**

- Passwords are hashed with argon2id via `argon2-cffi` 25.1, using the library defaults (`hash_password`, `verify_password`, `needs_rehash`).
- An `IdentityProvider` protocol in `packages/platform/auth/identity.py` has `authenticate(username, password) -> Principal | None` and `get_user(user_id) -> Principal | None`.
- The local implementation (`apps/api/identity_local.py`) reads users by username from the `users` collection through the user repository (a case-insensitive unique index on `username`).
- `IDENTITY_PROVIDER=local` selects it.
- If the username is unknown, the code still runs a dummy argon2 verify, so response time does not reveal whether the account exists.

**Rationale.** `security.md` lists argon2, scrypt and bcrypt, and argon2id is the current OWASP first choice. Constitution IX requires an interface with a fake implementation behind it.

**Alternatives.**

- `pwdlib`: another wrapper layer over argon2-cffi with no extra benefit.
- bcrypt: it has a 72-byte input limit and is weaker against GPU attacks.

## R6. System credential for agent tools (FR-000-22)

**Decision.**

- **Format.** A compact JWT, HS256, signed with `SYSTEM_CREDENTIAL_SECRET`, a separate key from `SESSION_SECRET`.
- **Claims.**
  - `typ="system"`, `aud="agent-tools"`, `sub="system:agent"`
  - `case_id`, `workflow_id`, `step`, `iat`, `exp`, `jti`
  - **no `role`**
- **Where it is minted.** Inside the agent-step activity, at the start of **each attempt**, with `exp = attempt start + start_to_close_timeout`.
  - It is passed straight to the agent call as the keyword-only argument `tool_credential`.
  - It is never returned from the activity, never written to Temporal history, and never logged.
- **Who verifies it.** `verify_system_credential(token, expected_case_id)` in `packages/platform/auth/tokens.py` is the only verifier, and MCP servers use it (005). It rejects:
  - a wrong `aud` or `typ`
  - an expired token
  - a mismatched `case_id`
  - user tokens
- The API rejects every `typ="system"` token on user routes.

**Rationale.**

- The workflow cannot sign a token: signing needs a secret and the wall clock, and TW-1 forbids both in workflow code.
- A separate "mint" activity would store the token in Temporal history.
- Minting per attempt keeps retries safe (TW-11).
- `exp` set to the step timeout means the credential expires when the step ends.
- Using one shared-secret algorithm for both token types keeps one code path (constitution X). The two token types differ by key, `typ` and `aud`.

**Alternatives.**

- Ed25519, where the worker signs and the MCP servers only verify: better if an MCP server were compromised, but every process reads the same local `.env`, so it gains nothing here. Can be swapped in later without changing the contract.
- A `jti` denylist checked at step end: `exp` already gives the required bound.

**Contract change.** The agent entry points in `specs/README.md` gain a keyword-only `tool_credential: str`, for example `verify_documents(case_id, *, tool_credential)`. This goes in the Day 1 contracts PR (BA-8).

## R7. Settings and fail-fast startup

**Decision.**

- One `Settings` class (`pydantic-settings` 2.16) lives in `packages/platform/settings.py`.
  - `extra="forbid"`; secrets are `SecretStr`.
  - Enums are `StrEnum`.
  - A model validator requires the credentials for the selected provider and mode.
- `load_settings()` catches `ValidationError`, prints **only** the setting names, the reason and the allowed values (never the values), and exits with code 2 (FR-000-04, US4 scenario 3).
- The full list is in [contracts/settings.md](contracts/settings.md). A test checks that `.env.example` lists exactly the settings fields (FR-000-03).
- `make setup` copies `.env.example` to `.env` if `.env` is missing, and fills the three generated secrets (`SESSION_SECRET`, `SYSTEM_CREDENTIAL_SECRET`, `DEMO_PASSWORD`) with random values. This supports SC-000-01.

**Rationale.** This meets FR-000-03 and FR-000-04 with one mechanism that every process (API, worker, MCP servers, seeds) uses.

**Alternative.** Settings per process: they drift apart. Rejected.

## R8. LLM provider selection and test modes (FR-000-12, FR-000-20)

**Decision.**

- There are two separate settings:
  - `LLM_PROVIDER` is `anthropic` or `bedrock`. Any other value refuses start-up and names the allowed values.
  - `LLM_MODE` is `live`, `recorded` or `fake`.
- **One module**, `packages/agents/llm/factory.py`, imports `langchain_anthropic`, `langchain_aws`, `anthropic` or `boto3` (AG-5, constitution VII). It builds:
  - `ChatAnthropic` (`langchain-anthropic` 1.7) for `anthropic`.
  - `ChatBedrockConverse` (`langchain-aws` 1.9) for `bedrock`.
  - `ReplayChatModel` for `recorded` and `fake`.
- Model IDs come from `ANTHROPIC_MODEL_ID` and `BEDROCK_MODEL_ID`.
- The client is created once per process (AG-9).
- No `temperature` or `top_p` (AG-7).
- A ruff `TID251` banned-API rule enforces the import ban, with an exception only for the factory file.
- CI and every test level except the live smoke test run with `LLM_MODE=fake`. Conftest fails if `CI=true` and `LLM_MODE=live`.

**Rationale.**

- The spec defines the provider as a choice between two real services. Faking is a separate question, and FR-009-09 needs a "recorded" demo switch that works with either provider.
- Using Converse for Bedrock means tool use, structured output and PDF blocks work the same way on both providers.

**Alternatives.**

- `LLM_PROVIDER=fake`: this mixes "which vendor" with "whether to call a vendor at all", and a recorded demo could not say which vendor the recording came from.
- `ChatBedrock` (the legacy API): it handles tool use and structured output differently from Anthropic.

**Operational input, not a blocker.** The exact Bedrock inference-profile ID and region for `claude-opus-5-5` come from the team member with Bedrock access. They go into their own `.env`, not into code.

## R9. Timeouts and retries (FR-000-13)

**Decision.**

- **HTTP calls.** `packages/platform/resilience.py` provides `call_with_retry(fn, *, timeout_s, max_attempts, retry_on)` written by hand (about 20 lines) so tests can inject the sleep and jitter: exponential backoff with jitter, a sleep the tests can inject, and an `httpx` client with `timeout` and `verify=True`.
- **Model calls.** The SDKs handle their own timeouts and retries:
  - Anthropic: `timeout=LLM_TIMEOUT_SECONDS`, `max_retries=LLM_MAX_RETRIES`.
  - Bedrock: botocore `Config(connect_timeout, read_timeout, retries={"max_attempts", "mode":"standard"})`.
  - No extra `.with_retry()` on top.
- **Temporal activities.** These use presets in `apps/worker/policies.py`:
  - `DEFAULT`: 30 s, 5 attempts, backoff 1 s → 30 s.
  - `AGENT_STEP`: 120 s, 3 attempts.
  
  In both, validation, permission and credential errors are non-retryable. An AST test checks that every `execute_activity` call uses a preset.
- **Database and Temporal clients.** Each sets a connect timeout. Start-up connects with bounded backoff.
- **Retry budget.** At most 3 activity attempts × (1 + `LLM_MAX_RETRIES`=2) SDK attempts, so no more than 9 model calls per step. This is documented in `policies.py`.

**Rationale.** This meets `security.md` and FR-000-13 without layered retries multiplying unseen.

**Alternative.** `tenacity` or `backoff`: rejected because a 20-line helper with an injectable sleep is simpler than a new direct dependency (constitution X).

## R10. Structured logging and PII masking (FR-000-10, FR-000-11)

**Decision.**

- `structlog` 26.1 writes JSON to stdout. The fields are listed in [contracts/logging.md](contracts/logging.md).
- `contextvars` carry `request_id`, `case_id`, `workflow_id` and `user_id`. Usernames are never logged.
- Standard-library logging, uvicorn and Temporal logs go through the same processor chain via `ProcessorFormatter`.
- A `mask_pii` processor masks:
  - values whose key is on a deny list (`name`, `first_name`, `last_name`, `address`, `dob`, `date_of_birth`, `ssn`, `identity_number`, `document_text`, `content`, `password`, `token`, `authorization`, `cookie`, …)
  - strings matching SSN-like or date-of-birth-like patterns
- Request and response bodies are never logged.
- The API middleware accepts an incoming `X-Request-ID` (a UUID) or generates `uuid4`, binds it, and echoes it in the response.
- The request ID is passed to Temporal: a client interceptor in `apps/api` sets the header `x-request-id`, and a worker inbound interceptor binds it for activities.

**Rationale.** PL-11 names structlog. Masking by key plus pattern catches both structured and accidental leaks. With one pipeline, uvicorn access logs are covered too.

**Alternative.** Masking only by key: a raw string such as an exception message could leak through.

## R11. Error format (FR-000-08)

**Decision.**

- Every 4xx and 5xx response uses the envelope `{"error": {"code", "message", "fields": [{"field","message","type"}], "reference_id"}}`, with the `X-Request-ID` header set to the same value.
- The codes are a closed set: `auth.required`, `auth.session_expired`, `auth.invalid_credentials`, `auth.forbidden`, `not_found`, `conflict`, `validation_failed`, `internal_error`, `dependency_unavailable`.
- Handlers cover `AppError` subclasses, `RequestValidationError`, `HTTPException` and bare `Exception`.
- A bare exception gets the generic message "Something went wrong." and the reference ID. The stack trace is logged under the same `request_id`, which meets SC-000-05.
- The envelope model lives in `packages/domain/errors.py`, so MCP servers return the same shape.

**Rationale.** One shape for the SPA's `ApiError`, the API tests and the MCP tools.

**Alternative.** RFC 9457 `application/problem+json`. It was considered and would work, but the spec's field names (code, message, field details, reference ID) map directly to the custom envelope, and `fields[]` is easier for the SPA to consume.

## R12. Health and readiness (FR-000-09)

**Decision.**

- Every component that is our code exposes `GET …/health` (liveness) and `GET …/ready` (dependencies), with the shapes in [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml).
- The API serves them at `/api/v1/health` and `/api/v1/ready`.
- The worker runs a small ASGI server on `WORKER_HEALTH_PORT` (8001) inside the same event loop.
- MCP servers serve them on their own ports (005).
- **Readiness statuses:**
  - `ready`: every check is ok.
  - `degraded`: only optional dependencies are down. Today that is tracing. Returns HTTP 200.
  - `not_ready`: a required dependency is down. Returns HTTP 503.
- **What the checks do:**
  - Each probe has a 2 s timeout.
  - The Mongo probe also confirms the synthetic marker exists (FR-000-14).
  - The worker's `ready` also needs the worker to be polling.
  - Temporal is checked with the client's `check_health()`, which lives only in `apps/api` and `apps/worker` (BA-7).
- **`make health`** (`scripts/check_health.py`) polls every component, including the Temporal dev server and Phoenix, and prints a table. It exits non-zero unless everything is ready or degraded.
- Responses never include connection strings or hosts.

**Rationale.** This covers US3 scenario 3, the "dependency down" edge case and the degraded-tracing rule in FR-000-28.

## R13. One-command run: processes, ports and the reset command (FR-000-01, FR-000-02)

**Decision.**

- **Native processes only (PR-5), started with `honcho`** (PL-12) from `Procfile` (dev) or `Procfile.prod` (`APP_ENV=prod`, the frontend built and served with `vite preview`, no reload).
- **MongoDB 8.0 is started by `make mongo-up`, not by honcho.** `mongod` runs forked, in the background, from the Homebrew binary as a single-node replica set (`rs0`) with authentication, with its data in `.data/mongo`. It is long-lived, and tests, `make reset` and `make dev` all need it. Replica-set mode is what makes multi-document transactions work (KD-10). `make mongo-down` stops it.
- **Processes in the Procfile:**

  | Process | Command | Port |
  |---|---|---|
  | `temporal` | `temporal server start-dev --db-filename .data/temporal.db` | 7233, UI 8233 |
  | `api` | uvicorn `apps.api.main:create_app --factory` | 8000 |
  | `worker` | `python -m apps.worker.main` | health on 8001 |
  | `phoenix` | `uvx --from arize-phoenix==21.0.0 phoenix serve` | 6006; data in `.data/phoenix` |
  | `web` | `pnpm --dir $BENEFIT_FE_DIR dev` (dev) or `preview` (prod) | 5173 or 4173 |

  MCP servers are added by 005 on ports 8101–8104.
- **`make reset`:**
  1. Calls K&D's `python -m db.seeds.reset`. It runs a safety guard (local host only, synthetic marker present or the database empty), then runs the migration runner `down` to base and `up` to head (which recreates every collection, validator and index), rebuilds DuckDB with the Mongo export and `dbt build`, seeds the data, and writes the marker.
  2. **Terminates every running Temporal workflow and deletes its schedules** in the namespace, using `temporal workflow terminate --query 'ExecutionStatus="Running"'`. The schedules are recreated when the worker starts.
  3. **Deletes the `benefit` Phoenix project** through Phoenix's REST API. If Phoenix is down, this step is skipped with a warning.
- **`make reset` works while the system is running** (US2 scenario 3).

**Rationale.**

- Deleting `.data/temporal.db` would require stopping the dev server, but the spec says reset runs against a running system.
- Terminating the workflows clears every in-flight case. Workflow IDs can be reused after termination.
- Old traces would otherwise point at case IDs that the deterministic seed creates again.

**Alternatives.**

- `docker compose`: forbidden by PR-5.
- Running `mongod` in the Procfile: it would stop with `make dev`, but tests and reset need it when the stack is down.
- `brew services start mongodb-community`: its shared config file has no replica set or authentication, and editing Homebrew's config makes setup fragile.

## R14. Data stores, versions and synthetic markers (FR-000-14, FR-000-24)

**Decision.**

| Store | Local (Homebrew) | CI (GitHub-hosted runner) | Synthetic marker |
|---|---|---|---|
| MongoDB 8.0 (single-node replica set `rs0`, auth on) | `mongodb/brew/mongodb-community@8.0` binary, started by `make mongo-up` | `mongodb-org` 8.0 from MongoDB's apt repository, started by the same `make mongo-up` | `_meta` document `{_id:"dataset", synthetic:true, …}` with a validator that requires `synthetic: true` |
| DuckDB (reporting) | `duckdb` Python package + `dbt-duckdb` (uv) | same | dbt model `meta.dataset_metadata`, built from the exported `_meta` document, with a dbt test for one row where `synthetic = true` |
| Temporal | `temporal` CLI (Homebrew, 1.8.x) | same CLI version installed in a setup step | n/a |

- `db/mongo/provision.py`, run once by `make mongo-up` over the localhost exception, initiates the replica set and creates the users and roles:
  - `benefit_owner`: `dbOwner` on the databases below. Runs migrations and reset only.
  - `benefit_app`: the runtime user. `readWrite` on `benefit`, and the custom role `auditAppend` (privileges `insert` and `find` on `benefit_audit.audit_log` only). The audit log has its own database because MongoDB cannot grant `readWrite` on a database while excluding one collection.
  - Each database has a `_test` twin (`benefit_test`, `benefit_audit_test`) that the integration tests reset freely, so running tests never touches development data.
- Authentication uses a generated keyfile in `.data/mongo/keyfile` (`make setup` creates it, mode 400). The two passwords are generated into `.env`.
- An integration test checks the major versions, so local and CI cannot drift apart.

**Rationale.** FR-000-24 requires matching major versions. Pinned service containers are allowed in CI only (PR-5).

## R15. Audit log (FR-000-23)

**Decision.**

- MongoDB collection `audit_log` in the database `benefit_audit`, created by the baseline migration, owned by K&D (see [data-model.md](data-model.md)).
- Its `$jsonSchema` validator has `additionalProperties: false` and **no free-text or nested-object field**, so personal data has nowhere to go.
- Append-only is enforced by database permissions (KD-12): `benefit_app` has the `auditAppend` role, so `insert` and `find` are allowed and `update`, `delete`, `drop` and `collMod` are refused with an authorization error. MongoDB has no triggers, so the owner user (`benefit_owner`, used for migrations and reset only) *can* change the collection. That is the one weaker point compared with PostgreSQL, and a test proves the app user cannot.
- Reset drops and recreates the collection with the owner user instead of deleting rows.
- A failed sign-in for an unknown username is recorded as `actor_type=anonymous`, with no `target_id`. The typed username is not stored.
- Times use the real clock, not the demo case clock, as BSON dates in UTC. The demo case clock is recorded by its own `demo_clock_advanced` action.
- The writer is `packages/platform/audit.py`, with a `MongoAuditWriter` that only does `insert_one`. It is shared by the API and the MCP servers (BA-3). When the audit entry belongs with another write (a caseworker action), the caller passes its transaction session.

**Rationale.** It fills every field FR-000-23 asks for, and leaves nowhere for personal data to be stored.

**Alternative.** A second append-only store (a log file or object storage): more moving parts for the same guarantee.

## R16. Household isolation in the repository layer (constitution VIII, draft amendment 2.0.0)

**Decision.**

- MongoDB has no row-level security, so isolation is enforced in one place, the repository layer.
- Every household-scoped collection carries `household_id` and `case_id` (required by its validator).
- Repository functions take a `Scope` built from the caller: a `Principal` (applicant, caseworker or supervisor) or the verified system credential (005). Applicants get a filter on their `household_id`. A system credential gets a filter on its `case_id`. Caseworkers and supervisors get no household filter.
- A repository call with no `Scope` raises `ScopeRequired`. There is no unscoped query helper to call by mistake. `tests/` includes a test that scans the repository modules for direct `find` calls on household-scoped collections outside the scoped helper.
- The API and the agent tools both use these repositories, so both are covered by the same checks.

**Rationale.** This keeps the defence-in-depth intent of the old row-level security as far as MongoDB allows. The cost is that the database no longer refuses an unscoped query by itself, so the scan test and the review rules (`database.md`) carry that weight.

**Alternative.** Per-household databases or collection views: heavy for four demo accounts and two households, and they break cross-household caseworker queries.

## R17. Local tracing (FR-000-28)

**Decision.**

- **Arize Phoenix 21** runs natively (`phoenix serve`, SQLite, OTLP and the UI on :6006). AG-15 and the BA runtime table both name it.
- **Instrumentation:** OpenInference `LangChainInstrumentor`, set up lazily inside `get_chat_model()` (BA-4).
- **Tags:** `agent_run_context(case_id, workflow_id, agent, prompt_version)` tags each run. `case_id` is used as the session ID, so traces can be searched by case (SC-000-09).
- **PII masking:** a deny-by-default `MaskingSpanExporter` keeps only allowlisted attributes: model, provider, token counts, cost, latency, tool name, prompt id and version, case and workflow IDs, and the validation outcome. It drops message content, input and output values, documents, and exception messages. The OpenInference `TraceConfig` hide flags are also turned on.
- **Exporter:** a `BatchSpanProcessor` with a bounded queue and a 2 s export timeout, so when Phoenix is down, runs continue and spans are dropped.
- **Off in CI:** `TRACING_ENABLED=false` there.
- **Cost:** computed in the app from `LLM_PRICE_*` settings, so it is the same across providers and matches `agent_runs`.

**Rationale.** It runs without Docker, OTLP is the standard, and a deny-by-default exporter makes it provable that traces contain no personal data.

**Alternatives.**

- Langfuse v3 self-hosted: needs ClickHouse, Redis and S3, which in practice means Docker.
- LangSmith: a cloud service, which breaks PR-5.

## R18. API contract generation and drift checks (FR-000-18, FR-000-26)

**Decision.**

- **In benefit-be:**
  - `scripts/export_openapi.py` writes `openapi/openapi.json` (sorted keys, 2-space indent) from `create_app()`, and the file is committed.
  - `make openapi-check` regenerates it and runs `git diff --exit-code`.
  - `tests/contract/test_openapi.py` compares the live schema with the committed one and names the differing paths.
- **In benefit-fe:**
  - `openapi/BE_COMMIT` pins a benefit-be SHA.
  - `scripts/gen-api.mjs` fetches `openapi/openapi.json` at that SHA (the repo is public, through raw.githubusercontent), vendors it to `openapi/openapi.json`, and runs `openapi-typescript` to produce `src/api/generated/schema.d.ts`.
  - `pnpm api:check` regenerates the client and fails on any diff.
- **The CI contract job in benefit-fe** also compares the vendored file with benefit-be's same-named branch, or with `main` if that branch doesn't exist. It fails if the vendored file is out of date.
- **Agent tool schemas:** snapshot tests in `tests/contract/` for each MCP tool's JSON Schema. The harness ships in 000; 005 adds the tool snapshots.

**Rationale.** Each side of FR-000-26 fails its own CI when it is out of date, and drift between the two repos fails in the frontend's contract job.

**Alternative.** `oasdiff` as a separate binary: not on PyPI, and a plain JSON diff with path naming is enough for an API that only one consumer uses.

## R19. CI pipeline (FR-000-16, FR-000-24, FR-000-25, SC-000-08)

**Decision.**

- **Setup:**
  - GitHub Actions on `ubuntu-24.04` hosted runners.
  - One `ci.yml` per repo, triggered by `pull_request` and by pushes to `main` and `feature/**` (so a branch is checked before its PR exists).
  - Actions are pinned by commit SHA.
  - `concurrency` cancels superseded runs.
  - Each job has `timeout-minutes`.
  - uv and pnpm caches are used.
  - Jobs run in parallel to stay under 15 minutes.
- **benefit-be jobs:**
  - `static`: ruff check and format, `mypy --strict`, `pip-audit`, `gitleaks`.
  - `unit`
  - `workflow`: the Temporal time-skipping environment, with the test-server binary cached.
  - `contract`
  - `integration`:
    - MongoDB 8.0 installed from MongoDB's apt repository and started with `make mongo-up`, plus the Temporal CLI dev server.
    - Settings: `EMBEDDER=fake`, `RERANKER=fake`, `LLM_MODE=fake`, `TRACING_ENABLED=false`.
    - Runs `make reset` with a random `DEMO_PASSWORD`, then `pytest -m integration`.
  - `e2e`
- **benefit-fe jobs:**
  - `static`: ESLint, Prettier, `tsc --noEmit`, `pnpm audit --audit-level high`, gitleaks.
  - `unit`: Vitest.
  - `contract`
  - `e2e`
- **The `e2e` job, in both repos:**
  1. Checks out both repos.
  2. Picks the sibling repo's ref with `scripts/ci/resolve-sibling-ref.sh`: the same branch name if `git ls-remote --heads` finds it, otherwise `main`. The chosen ref is written to the job summary.
  3. Starts the stack with `Procfile.ci`, which has no Phoenix.
  4. Waits with `scripts/ci/wait-ready.sh`, then runs the `stack` and `api` tests (`pytest -m "stack or api"`) against the running stack.
  5. Runs Playwright on Chromium, uploading the HTML report and traces as artifacts.
  
  Firefox and WebKit run in `nightly.yml` on `main`.
- **Merge blocking:** branch protection marks every job as required. That is set up by 009 (FR-009-02), which must land before the first feature PR.

**Rationale.**

- Both repos are public (GitHub API returned 200 on 2026-11-09), so the sibling checkout needs no token.
- Service containers are allowed in CI only (PR-5).

## R20. End-to-end suite (FR-000-19, FR-000-20, FR-000-25)

**Decision.**

- The suite lives in `benefit-fe/e2e/` (FR-000-25), with Page Object Model pages in `e2e/pages/` and a fixture that runs axe checks.
- `auth.setup.ts` signs in once per role through the API and saves `storageState` to `e2e/.auth/<role>.json`, which is git-ignored.
- `sign-in.spec.ts` covers the 000 scenarios that run today.
- The six journeys from FR-000-19 each get a spec file now, marked `test.fixme()` with the annotation `{type: 'pending', description: '<FR ids>; built by <feature>'}`:

  | File | Built by |
  |---|---|
  | `mismatch-request-info.spec.ts` | 002/011 |
  | `restart-resume.spec.ts` | 001 |
  | `missed-deadline-override.spec.ts` | 011/010 |
  | `automatic-renewal.spec.ts` | 007 |
  | `renewal-one-document.spec.ts` | 007 |
  | `applicant-blocked-other-household.spec.ts` | 001/005 |

  This way they show up as pending and are not silently skipped. 009's traceability report reads this annotation.
- The backend runs with `LLM_MODE=fake` (FR-000-20).
- `timezoneId: 'America/Chicago'`.
- Retries are 2 in CI and 0 locally.

## R21. Time zone (FR-000-27)

**Decision.**

- **Storage:** timestamps are stored as UTC BSON dates. Dates and day counts are calculated in `America/Chicago`.
- **Backend:** `packages/platform/clock.py` provides:
  - a `Clock` protocol with `SystemClock` and `FixedClock`
  - `CHICAGO = ZoneInfo("America/Chicago")`
  - `today(clock)`, `to_local(dt)` and `days_between(a, b)`
  
  `tzdata` is pinned so macOS and Linux give the same results.
- **Workflows:** use `apps/worker/workflows/calendar.py`, which only takes `workflow.now()`. The zone is loaded through the sandbox pass-through, so no zoneinfo files are read inside workflow code (TW-1).
- **Frontend:** `src/lib/time.ts` formats with `Intl.DateTimeFormat(…, {timeZone: 'America/Chicago'})`. Vitest and Playwright run with `TZ` and `timezoneId` set to Chicago.

**Rationale.** One zone everywhere, with injected clocks so tests are deterministic (`testing.md`).

## R22. Demo accounts and passwords (FR-000-05, FR-000-21)

**Decision.**

- **Seeded accounts:**
  - `applicant1` (household A)
  - `applicant2` (household B, needed for the isolation journey)
  - `caseworker1`
  - `supervisor1`
- **Passwords:**
  - All four accounts use one shared `DEMO_PASSWORD` from `.env`. It is left blank in `.env.example`, and seeding fails if it is unset.
  - CI generates a random value for each run.
  - The seed hashes it with argon2id at seed time. **Neither the plaintext nor the hashes are committed.**
- **Roles:** `supervisor` includes `caseworker` (`packages/platform/auth/roles.py`). Supervisor-only actions (demo clock, escalated-task view) are checked with `require_roles(Role.supervisor)`.

**Rationale.** One value is easy to share for the demo and keeps gitleaks clean. FR-000-05 only asks for accounts per role.

**Alternative.** A password per role: more settings for no requirement.

## R23. Delivery: contracts PR vs feature PR

**Decision.**

- **Day 1 contracts PR** (all lanes, reviewed by everyone; constitution VI):
  - `packages/domain` models: `auth`, `audit`, `errors`, `health`, `SystemCredentialClaims`, `AgentRunContext`, `AgentRunUsage`.
  - The **`0001_baseline`** migration (K&D), which includes the 000 tables.
  - `contracts/rest-api.openapi.yaml`, turned into `openapi/openapi.json`.
  - The `tool_credential` change to the agent entry-point signatures.
- **Rest of 000** (settings, auth, errors, logging, health, Makefile, Procfile and CI in benefit-be, plus the shell, sign-in and e2e harness in benefit-fe): goes in the `feature/000-platform-foundations` PRs in each repo, linked to each other.
- **Commits:** each lane's files go in its own commits, per the ownership table in `backend-architecture.md`.

**Rationale.** The spec says 000 is part of the Day 1 contracts PR. Splitting the contract parts from the implementation keeps the contract review small.

## R24. SYNTHETIC marker on generated documents (FR-000-14)

**Decision.**

- **Helper module.** `packages/platform/synthetic.py` is the only place that marks a document. It provides:
  - `SYNTHETIC_LABEL = "SYNTHETIC – NOT A REAL DOCUMENT"`
  - `stamp_pdf(data: bytes) -> bytes`: overlays a visible label band in the top and bottom margins of every page (reportlab overlay merged with pypdf) and sets the PDF metadata `Subject`/`Keywords` to `SYNTHETIC`.
  - `stamp_image(data: bytes) -> bytes`: adds a margin band with the label to PNG and JPEG images (Pillow) and writes the label into the PNG text chunk or JPEG comment.
  - `stamp_text(text: str) -> str`: prefixes plain-text and HTML notice bodies with a label line (or a banner `<div role="note">`).
  - `is_marked(data: bytes, media_type: str) -> bool`: used by tests and the reset check. It reads the metadata or comment, and for PDFs it also extracts the text to confirm the label is on the page.
- **Who calls it.**
  - The seed generator (003) stamps every document it writes to `db/seeds/generated/`: pay stubs, identity documents and scans.
  - Notice rendering (011) stamps every notice and drafted request before it is stored or shown.
  - 000 ships the helper and its tests. The features that generate documents call it.
- **Where the label goes.** The label sits in a margin band, never over the body, so the AI extraction in 002 still reads the document content. The 002 extraction evals run on stamped documents, so any effect shows up in the scores.
- **Enforcement.**
  - `tests/db/seeds/test_generated_documents.py::test_FR_000_14_every_generated_document_is_marked` scans `db/seeds/generated/` after `make seed`.
  - `BlobStore.put` (KD-14) logs a warning and refuses documents from a generator source that are not marked.
  - Applicant uploads in the demo are themselves seeded files, so they are already marked.

**Rationale.** FR-000-14 needs a visible marker on every generated document. One helper means one look and one checker across 001, 003 and 006. Margin placement protects extraction quality.

**Dependencies.**
- `pypdf` 7.0 and `reportlab` 5.1: 003 already needs these to generate pay-stub PDFs.
- `Pillow` 13.0: scanned and photo variants.

All three are pinned exactly (PR-4).

**Alternatives.**
- Each generator draws its own label. Rejected: the labels would differ and there would be no single checker.
- A diagonal watermark across the page. Rejected: it covers the values that 002 extracts.
- Metadata only. Rejected: the spec requires a *visible* marker.

## R25. Keeping CI under 15 minutes (SC-000-08)

**Decision.** The `e2e` job is the slowest. These steps keep it within budget:

1. Jobs run in parallel. `e2e` runs alongside the other jobs, not after them.
2. Caches cover:
   - uv
   - the pnpm store
   - Playwright browsers, keyed on the Playwright version
   - the Temporal CLI binary and test server
3. The frontend is built once in the job with `vite build`. The job then serves the build with `vite preview` (`Procfile.ci`) instead of starting the dev server.
4. Only Chromium runs on PRs. Firefox and WebKit run nightly.
5. `fullyParallel: true`, with 2 workers.
6. Every CI job has `timeout-minutes` (e2e: 12; the others: 8).
7. **Fallback if a green run goes over 15 minutes.** Tag the journeys `@smoke` or `@full`. PRs run only `@smoke` (sign-in plus one journey per built feature), and `@full` runs on `main` and nightly. This is allowed by `quality-testing-playwright.md` ("run `@smoke` on every PR when the full suite is too slow").
   - The fallback only switches on if the 009 factory dashboard shows the median e2e job time over 10 minutes.

**Rationale.** SC-000-08 is a hard target, and the e2e job starts the whole stack. The fallback keeps the gate in place while trimming what it runs on PRs.

**Alternative.** Sharding e2e across runners. Rejected: each shard would start its own stack, and for six journeys the startup time outweighs the gain.

## R26. Assumptions to verify early (first tasks)

These are believed to be true but have not been checked yet. `/speckit-tasks` should make each one an early task with a fallback, so a wrong assumption doesn't stall later work.

| # | Assumption | How to check | Fallback if false |
|---|---|---|---|
| V1 | Phoenix 21 can delete a project through its REST API (`DELETE /v1/projects/{name}`), so traces can be cleared without a restart | Call it against a local `phoenix serve` | `make reset` warns and deletes `.data/phoenix` only when Phoenix is stopped. The quickstart notes the restart. |
| V2 | The Homebrew `mongodb-community@8.0` binary starts as a single-node replica set with a keyfile and authentication, and `provision.py` can create the users over the localhost exception | Run `make mongo-up` on a clean `.data/mongo` | **Verified 2026-11-09 on MongoDB 8.0.34.** `replSetInitiate` and the first `createUser` work over the localhost exception, but the first user may only hold `userAdminAnyDatabase` (a first user with other roles gets "not authorized"). `provision.py` creates it minimal, then grants the rest after authenticating. |
| V3 | ESLint 10 works with typescript-eslint 8.72, eslint-plugin-react-hooks and jsx-a11y | `pnpm lint` on the app shell | **Not true: verified 2026-11-09.** `eslint-plugin-jsx-a11y` 6.10.2 supports ESLint only up to 9, so ESLint is pinned to 9.39.5. typescript-eslint 8.72.2 works with it. |
| V4 | `langchain-anthropic` 1.7 and `langchain-aws` 1.9 both give native JSON-schema structured output without forcing tool choice (AG-6) | `make smoke-ai` on each provider | `bind_tools(tool_choice="auto")` plus `PydanticToolsParser` inside the `structured()` helper |
| V5 | The Temporal CLI version on Homebrew (1.8.x) is installable at the same version in CI | Pin the version in the setup step | **Verified.** Homebrew has 1.8.2 and `TEMPORAL_CLI_VERSION := 1.8.2` is set in the Makefile. CI installs that release. |
| V6 | The replay test (TW-14) has a recorded history to replay | Record `histories/smoke_v1.json` after the first green time-skipping run | None needed. This is an ordering constraint: the replay test task depends on the smoke workflow task. |

## R27. MongoDB as the only operational database (draft constitution 2.0.0)

**Decision.** The team chose to run everything on MongoDB 8.0 and drop PostgreSQL. This replaces PostgreSQL, pgvector, Alembic, SQLAlchemy and asyncpg. It is a **draft amendment**: `.specify/memory/constitution.md` is marked "DRAFT AMENDMENT v2.0.0" and takes effect only when all three team members approve the PR (Governance). If the team rejects it, R13–R16, R22 and the database tasks go back to the PostgreSQL design from version 1.4.1.

| Was (PostgreSQL) | Now (MongoDB) |
|---|---|
| Tables, enums, CHECK and foreign keys | Collections with `$jsonSchema` validators (required fields, enums, patterns, `additionalProperties: false`) and unique indexes. The applicant-needs-a-household rule is a validator `oneOf`. |
| Alembic migrations | Versioned scripts in `db/migrations/versions/` with `upgrade(db)` and `downgrade(db)`, applied by `db/migrate.py`, which records them in `_migrations` (KD-11) |
| Row-level security | Repository-layer `Scope` filters (R16) |
| Append-only audit log by grants and triggers | Restricted `auditAppend` role for the runtime user (R15) |
| `SECURITY DEFINER` sign-in lookup | The user repository, by username (case-insensitive unique index) |
| pgvector HNSW and Postgres full-text search | In-application cosine plus BM25 over passages cached once per process (KD-5, owned by 004) |
| DuckDB reads Postgres directly | An export step copies pseudonymised collections into DuckDB, then dbt builds (KD-15, owned by 008) |
| Single transaction across tables | Multi-document transactions, which need the replica set `make mongo-up` starts (KD-10) |

**Rationale.** One database is one fewer service to install, start, version-match in CI and reset, and the data is document-shaped. The costs are listed in the table: no database-enforced household isolation, and an owner user that can edit the audit log, so those two guarantees now depend on repository code and tests.

**Not changed by this decision.** The API and tool contracts, the roles and sessions, the error format and the test levels do not change.

**Alternatives.**

- Keep both databases (the version 1.4.1 design). Kept as the fallback if the amendment is rejected.
- MongoDB's own vector search for policy search: it needs the extra `mongot` search process and was rejected for 004. The manual has only 25–40 sections, so in-app search is enough.

## Clarifications resolved

Every open question from the lane sections has a decision above. None remain open.

| Question (lane) | Resolution |
|---|---|
| Cookie or bearer token; server-side revocation (Platform) | R4 |
| `LLM_PROVIDER=fake` or a separate `LLM_MODE` (Agents) | R8 |
| TypeScript 7 support (Platform) | R3: pin 5.9.3 |
| Router; whether to drop oxlint (Platform) | R1, R3 |
| Python 3.11 or 3.12 (Workflows) | R2: 3.12 |
| Credential end-of-step mechanism and signing algorithm (Workflows) | R6 |
| Request-ID header to Temporal (Workflows) | R10: `x-request-id` header via interceptors |
| Worker readiness scope and port (Workflows, Platform) | R12: Temporal + PG + Mongo + polling; port 8001 |
| Whether reset clears Temporal and traces (Workflows, K&D) | R13 |
| Audit timestamps: real clock or case clock (K&D) | R15: real clock |
| One `DEMO_PASSWORD` or one per role (K&D) | R22: one |
| One baseline migration or several (K&D) | R23: a single `0001_baseline` in the contracts PR |
| pgvector trust (K&D) | Removed: PostgreSQL is no longer used (draft constitution 2.0.0). Policy search runs in the application (KD-5). |
| Sibling-repo token (Platform) | R19: not needed, both repos are public |
| Cost source (Agents) | R17: in-app `LLM_PRICE_*` |
| Retry budget across the SDK and Temporal (Agents, Workflows) | R9 |
| Case-clock offset location (Workflows) | Out of scope for 000. 001 builds it on `calendar.py` (FR-001-13). |
| SYNTHETIC marker on generated documents (gap found on re-check) | R24 |
| CI time budget fallback (gap found on re-check) | R25 |
| Assumptions that have not been checked yet | R26 lists them as early verification tasks |

## Inputs still needed from people (not blocking `/speckit-tasks`)

| # | Input | From | Needed by |
|---|---|---|---|
| P1 | Bedrock inference-profile ID and region for `claude-opus-5-5` | The team member with Bedrock access, set in their own `.env` | SC-000-04: `make smoke-ai` on Bedrock |
| P2 | Branch protection with the CI job names as required checks, in both code repos | A repo admin, through 009 (FR-009-02) | FR-000-16 merge blocking, SC-000-06. Must be in place before the first feature PR. |
| P3 | Tick the 000 items under "Spec review round 2" in `specs/README.md` (FR-000-14, FR-000-22 to FR-000-26, FR-000-28) | All three team members, in the contracts PR review | Before the Day 1 contracts PR merges |
| P4 | Order of the contracts PR versus 000. The `users` and `audit_log` collections come from K&D's `0001_baseline`, so sign-in can't merge before it. | The team, on Day 1 morning | Before the lanes split |
| P5 | Approve the draft constitution amendment 2.0.0 (MongoDB as the only database, no row-level security) | All three team members, by PR | Merging any MongoDB-only database work, and the changes to `project-rules/` and `specs/README.md` |
