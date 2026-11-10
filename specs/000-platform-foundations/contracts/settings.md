# Contract: settings (`.env`)

These are all the settings the `benefit-be` processes read, through one `Settings` class in `packages/platform/settings.py` (FR-000-03, FR-000-04, R7).

- `.env.example` is committed and lists every setting below, with secrets left blank. A test checks the two match.
- `.env` is git-ignored.
- `make setup` creates `.env` and fills in the secrets marked **generated**.

## Start-up behaviour

`load_settings()` checks every field. On any missing or invalid setting it:

- prints one line per problem: `setting <NAME>: <reason>; allowed: <values>`
- never prints the value itself
- exits with code **2**

For example: `setting LLM_PROVIDER: invalid value; allowed: anthropic, bedrock` (US4 scenario 3).

## Runtime and stores

| Setting | Type / allowed | Default | Notes |
|---|---|---|---|
| `APP_ENV` | `dev`, `prod`, `test` | `dev` | `prod` is the production-like local profile (`make prod`). It turns off reload and debug. The session cookie gets the `Secure` flag when `WEB_ORIGIN` is also https. |
| `DEMO_PROFILE` | bool | `true` in dev | Turns on demo-only behaviour owned by other features (FR-001-13 demo clock, faster metrics refresh) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | |
| `LOG_FORMAT` | `json`, `console` | `json` | `console` is for local debugging only. The fields are the same either way. |
| `API_PORT` | int | `8000` | |
| `WORKER_HEALTH_PORT` | int | `8001` | |
| `WEB_ORIGIN` | URL | `http://localhost:5173` | Used in prod-like mode to check `Origin` on state-changing requests |
| `BENEFIT_FE_DIR` | path | `../benefit-fe` | Where `make dev`/`prod`/`e2e` find the frontend |
| `MONGO_URL_APP` | SecretStr, mongodb URL | **generated** (`make setup`) | Runtime user `benefit_app`: `readWrite` on `MONGO_DB`; `insert` and `find` only on `MONGO_AUDIT_DB.audit_log`. Includes `replicaSet=rs0` and `authSource=admin`. |
| `MONGO_URL_OWNER` | SecretStr, mongodb URL | **generated** (`make setup`) | User `benefit_owner` (`dbOwner`). Used for migrations, reset and provisioning only. |
| `MONGO_DB` | str | `benefit` | Main database. A `benefit_test` twin is used by the integration tests. |
| `MONGO_AUDIT_DB` | str | `benefit_audit` | Holds only `audit_log`, so the runtime user can be limited to insert and find. A `benefit_audit_test` twin is used by tests. |
| `MONGO_DATA_DIR` | path | `.data/mongo` | Where `make mongo-up` keeps the data, the keyfile and the log |
| `DUCKDB_PATH` | path | `.data/reporting.duckdb` | |
| `TEMPORAL_ADDRESS` | host:port | `localhost:7233` | |
| `TEMPORAL_NAMESPACE` | str | `default` | |
| `TEMPORAL_TASK_QUEUE` | str | `benefit-case` | |
| `HTTP_TIMEOUT_SECONDS` | float > 0 | `10` | Default for outbound HTTP calls (FR-000-13) |
| `HTTP_MAX_ATTEMPTS` | int 1–5 | `3` | |

## Identity and sessions

| Setting | Type / allowed | Default | Notes |
|---|---|---|---|
| `IDENTITY_PROVIDER` | `local` | `local` | Constitution IX. `local` reads seeded users. |
| `SESSION_SECRET` | SecretStr, ≥ 32 bytes | **generated** | Signs user session JWTs |
| `SESSION_TTL_HOURS` | int 1–24 | `8` | FR-000-07 |
| `SYSTEM_CREDENTIAL_SECRET` | SecretStr, ≥ 32 bytes, ≠ `SESSION_SECRET` | **generated** | Signs agent tool credentials (FR-000-22) |
| `DEMO_PASSWORD` | SecretStr, ≥ 12 chars | **generated** | Read only by the seed command and the Playwright setup. Seeding refuses to run if it is empty. |

## AI provider and modes

| Setting | Type / allowed | Default | Notes |
|---|---|---|---|
| `LLM_PROVIDER` | `anthropic`, `bedrock` | `anthropic` | FR-000-12. Only `packages/agents/llm/factory.py` reads it to pick an SDK. |
| `LLM_MODE` | `live`, `recorded`, `fake` | `fake` | `recorded` is FR-009-09. `test` and CI require `fake`. `live` with `CI=true` is refused. |
| `ANTHROPIC_API_KEY` | SecretStr | (blank) | Required when `LLM_PROVIDER=anthropic` and `LLM_MODE=live` |
| `ANTHROPIC_MODEL_ID` | str | `claude-opus-5-5` | AG-5 |
| `AWS_REGION` | str | (blank) | Required when `LLM_PROVIDER=bedrock` and `LLM_MODE=live` |
| `AWS_PROFILE` | str | (blank) | Optional. Otherwise the standard AWS credential chain is used. |
| `BEDROCK_MODEL_ID` | str | (blank) | Required when using Bedrock live. The inference-profile ID for the same Claude model. |
| `LLM_TIMEOUT_SECONDS` | float > 0 | `60` | FR-000-13 |
| `LLM_MAX_RETRIES` | int 0–3 | `2` | SDK retries, within the activity retry budget (R9) |
| `LLM_MAX_TOKENS` | int | `4096` | |
| `LLM_RECORDINGS_DIR` | path | `tests/fixtures/llm` | Fixture and recording store for `recorded` and `fake` |
| `LLM_PRICE_INPUT_PER_MTOK` | decimal | (blank) | USD per million input tokens, for trace cost |
| `LLM_PRICE_OUTPUT_PER_MTOK` | decimal | (blank) | USD per million output tokens, for trace cost |
| `MCP_TOOL_TIMEOUT_SECONDS` | float > 0 | `15` | Used by 005 |

## Retrieval models

| Setting | Type / allowed | Default | Notes |
|---|---|---|---|
| `EMBEDDER` | `qwen`, `fake` | `qwen` (dev), `fake` (test/CI) | FR-000-24. `make eval` refuses `fake`. |
| `RERANKER` | `bge`, `fake` | `bge` (dev), `fake` (test/CI) | |

## Tracing

| Setting | Type / allowed | Default | Notes |
|---|---|---|---|
| `TRACING_ENABLED` | bool | `true` (dev/prod), `false` (test/CI) | FR-000-28 |
| `TRACING_OTLP_ENDPOINT` | URL | `http://localhost:6006/v1/traces` | Phoenix |
| `TRACING_PROJECT` | str | `benefit` | Phoenix project. `make reset` deletes it. |

## Cross-field validation

- `SESSION_SECRET != SYSTEM_CREDENTIAL_SECRET`.
- When `LLM_MODE=live`:
  - `LLM_PROVIDER=anthropic` requires `ANTHROPIC_API_KEY`.
  - `LLM_PROVIDER=bedrock` requires `AWS_REGION` and `BEDROCK_MODEL_ID`.
- `APP_ENV=test` requires `LLM_MODE=fake`, `EMBEDDER=fake`, `RERANKER=fake` and `TRACING_ENABLED=false`.

## Frontend (`benefit-fe/.env.example`)

| Setting | Default | Notes |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | Target of the Vite dev and preview proxy for `/api` |
| `E2E_BASE_URL` | `http://localhost:5173` | Playwright |
| `E2E_APPLICANT_USERNAME`, `E2E_APPLICANT2_USERNAME`, `E2E_CASEWORKER_USERNAME`, `E2E_SUPERVISOR_USERNAME` | `applicant1`, `applicant2`, `caseworker1`, `supervisor1` | |
| `E2E_PASSWORD` | (blank) | The same value as the backend `DEMO_PASSWORD` |
