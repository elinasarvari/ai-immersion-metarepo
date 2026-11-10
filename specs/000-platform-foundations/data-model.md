# Data Model: Platform Foundations (000)

Entities from [spec.md](spec.md) "Key Entities", plus the structural records this feature needs.

The shared Pydantic models go in `benefit-be/packages/domain/` through the Day 1 contracts PR (BA-6, BA-8). The MongoDB collections, validators and indexes go in Knowledge & data's `db/migrations/versions/0001_baseline.py` (draft constitution 2.0.0: MongoDB is the only operational database, R27).

Conventions:
- Timestamps are BSON dates in UTC. Dates and day counts are computed in America/Chicago (FR-000-27).
- IDs are UUIDs (`_id` is the UUID, stored as a BSON UUID). Seeded IDs are `uuid5` values from the fixed seed namespace, so `make reset` recreates them.
- No entity below holds names, addresses, dates of birth, identity numbers or document contents, apart from `users.display_name`, which is a synthetic label such as "Caseworker One".

---

## Role (enum)

`packages/domain/auth.py`: `class Role(StrEnum)`. Stored as a string enum in the `users` validator.

| Value | Can do |
|---|---|
| `applicant` | Only their own household's records (FR-000-05, constitution VIII) |
| `caseworker` | Every case. Caseworker actions. |
| `supervisor` | Everything a caseworker can do, plus the demo clock (FR-001-15) and the escalated-task view (FR-006-01) |

`packages/platform/auth/roles.py` holds the role hierarchy: `implies(supervisor) ⊇ {caseworker}`. The system credential is **not** a role (FR-000-22).

## User

MongoDB collection `users`. Domain models: `UserPublic` (returned by the API) and `Principal` (the authenticated caller).

| Field | Type | Rules |
|---|---|---|
| `_id` | UUID | Seeded with uuid5 |
| `username` | string, required | 1–64 chars, `^[a-z0-9_.-]+$`. A synthetic handle (`caseworker1`). **Unique index with collation strength 2** (case-insensitive). |
| `display_name` | string, required | A synthetic label, never a realistic person name |
| `password_hash` | string, required | Validator pattern `^\$argon2id\$` (FR-000-21). Never returned or logged. |
| `role` | string enum, required | `applicant`, `caseworker` or `supervisor` |
| `household_id` | UUID or null | Validator: required and non-null when `role == "applicant"`, absent or null otherwise |
| `created_at` | date, required | |

- Validator: `additionalProperties: false`.
- Sign-in reads a user by username through the user repository, projecting only `_id`, `password_hash`, `role`, `household_id` and `display_name`. The runtime user `benefit_app` has `readWrite` on this collection.
- Seeded accounts (R22): `applicant1` (household A), `applicant2` (household B), `caseworker1`, `supervisor1`. They share one password, `DEMO_PASSWORD`, hashed at seed time.
- `UserPublic`: `{id, username, display_name, role, household_id | null}`.
- `Principal`: `{user_id, role, household_id | null, session_expires_at}`, built from a verified session token.

## Household (stub in 000)

MongoDB collection `households`: `_id` (UUID), `created_at` (date). 000 only creates what `users.household_id` refers to. 003 adds the household attributes in the same baseline (contracts PR).

## Session

Not stored. It is a signed JWT in the `benefit_session` cookie (R4).

| Claim | Meaning |
|---|---|
| `typ` | Always `"user"` |
| `sub` | User id |
| `role` | `Role` |
| `hh` | Household id; applicants only |
| `iat`, `exp` | Issued and expiry, as Unix seconds. `exp = iat + SESSION_TTL_HOURS·3600`, default 8 h (FR-000-07). |
| `jti` | Random id, used for log correlation only |

**Lifecycle:**

```
(none) --POST /auth/login ok--> active --now >= exp--> expired
active --POST /auth/logout--> (none)        expired --any protected call--> 401 auth.session_expired
(none) --any protected call--> 401 auth.required
```

**Validation:**
- HS256 with `SESSION_SECRET`, and `typ == "user"`.
- No leeway on `exp`.
- The user must still exist. `IdentityProvider.get_user` is called only for `/auth/me`. Other routes trust the token until it expires.

## System credential

Not stored. The domain model `SystemCredentialClaims` is used by the worker activity, which issues it, and by the MCP servers, which verify it (R6, FR-000-22).

| Claim | Meaning |
|---|---|
| `typ` | Always `"system"` |
| `aud` | Always `"agent-tools"` |
| `sub` | Always `"system:agent"` |
| `case_id` | The one case this credential is good for |
| `workflow_id`, `step` | For tracing and audit |
| `iat`, `exp` | `exp = attempt start + activity start_to_close_timeout` |
| `jti` | New for each activity attempt |

**Rules:**
- It is signed with `SYSTEM_CREDENTIAL_SECRET`.
- It has no `role` claim.
- The verifier rejects:
  - an `aud` other than `agent-tools`
  - a `typ` other than `system`
  - an expired token
  - a `case_id` that doesn't match the requested case
- The API rejects every `typ=system` token.
- It is never written to Temporal history, logs, traces or `tool_calls`. Only its `jti` may be recorded, as the audit `actor_id`.

## Audit log entry

MongoDB collection `audit_log` in its own database `benefit_audit` (`MONGO_AUDIT_DB`), append-only (KD-12, R15). It has its own database because MongoDB cannot grant `readWrite` on a database while excluding one collection. Domain model `AuditLogEntry`, with the enums `AuditAction`, `ActorType` and `AuditOutcome` (FR-000-23).

| Field | Type | Rules |
|---|---|---|
| `_id` | ObjectId | Generated on insert. Sorts by insertion time. |
| `occurred_at` | date, required | Real time, not the demo case clock (R15) |
| `actor_type` | string enum, required | `user`, `system`, `anonymous`. `anonymous` is used only for failed sign-ins of unknown users |
| `actor_id` | string or absent | User UUID, or system credential `jti`. Absent when `anonymous`. Never a username. |
| `actor_role` | string enum or absent | Role at the time of the action |
| `action` | string enum, required | See the list below |
| `target_type` | string or absent | `case`, `user`, `route`, `tool`, `clock`, `metrics`, `household` |
| `target_id` | string or absent | Case or user UUID, route template, or tool name. Never personal data. |
| `outcome` | string enum, required | `success`, `failure`, `refused` |
| `reason_code` | string enum or absent | From a fixed set: `invalid_credentials`, `role_not_allowed`, `wrong_household`, `wrong_case`, `credential_expired` |
| `reference_id` | string, required | The request or reference ID, which links to the log entry (SC-000-05) |

**`action` values** (FR-000-23):
- `sign_in` (outcome `success` or `failure`)
- `access_refused` (API route or agent tool)
- `caseworker_action`
- `demo_clock_action`
- `redetermination_started_on_demand`
- `metrics_refreshed`

**Enforcement:**
- The validator has `additionalProperties: false`, string lengths capped at 128, and no object or array field, so there is no free-text or nested field.
- `benefit_app` has `readWrite` on `benefit` and the custom role `auditAppend` on `benefit_audit.audit_log` (`insert` and `find` only). `update`, `delete`, `drop` and `collMod` are refused. The owner user can modify it (R15).
- Indexes are on `{target_type: 1, target_id: 1, occurred_at: 1}` and on `{occurred_at: 1}`.

## Error (envelope)

Domain model `ErrorEnvelope` in `packages/domain/errors.py`. The full schema is in [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml) (FR-000-08).

| Field | Type | Rules |
|---|---|---|
| `error.code` | `ErrorCode` enum | `auth.required`, `auth.session_expired`, `auth.invalid_credentials`, `auth.forbidden`, `not_found`, `conflict`, `validation_failed`, `internal_error`, `dependency_unavailable` |
| `error.message` | `str` | Readable, fixed per code for 5xx. No stack traces, SQL, hosts or input values. |
| `error.fields` | `list[FieldError]` | Present (may be empty) on every error; filled for `validation_failed`. `FieldError = {field: "body.username", message, type}`. Never echoes the input value. |
| `error.reference_id` | `str` (UUID) | The same value as the `X-Request-ID` response header and the log `request_id` |

## Health and readiness reports

Domain models `HealthReport` and `ReadinessReport` in `packages/domain/health.py`. Every component that is our code returns these shapes (R12, FR-000-09).

- `HealthReport`: `{component: str, status: "ok", version: str, synthetic_data: true}`.
- `ReadinessReport`: `{component, status: ReadinessStatus, checks: [{name, status: CheckStatus, required: bool}]}`.
  - `CheckStatus` is `ok`, `down` or `degraded`.
  - `ReadinessStatus` is derived from the checks:
    - `not_ready` if any required check is `down`.
    - Otherwise `degraded` if any check is not `ok`.
    - Otherwise `ready`.
  - HTTP status is 503 only for `not_ready`.

| Component | Required checks | Optional checks |
|---|---|---|
| api | `mongo` (and marker), `temporal` | `tracing` |
| worker | `temporal`, `mongo`, `polling` | `tracing` |
| mcp servers (005) | the store each one owns | `tracing` |

## Synthetic data marker (per store)

Domain model `DatasetMetadata`: `{synthetic: true, seed: int, generator_version: str, generated_at: datetime}` (FR-000-14).

| Store | Where it lives | Enforcement |
|---|---|---|
| MongoDB | Collection `_meta`, document `{_id: "dataset", synthetic: true, seed, generator_version, generated_at}` | `$jsonSchema` validator requires `synthetic: true`. Readiness probe. |
| DuckDB | dbt model `meta.dataset_metadata`, built from the exported `_meta` document | dbt test: exactly 1 row, `synthetic = true` |

## Generated document marker

Applies to every generated document (FR-000-14, R24). Individual database records do not need their own marker.

| Document kind | Produced by | Marker |
|---|---|---|
| PDF (pay stubs, identity docs, PDF notices) | 003 seeds, 001/006 notices | A visible label band in the top and bottom margins of every page, plus PDF metadata `Subject`/`Keywords` = `SYNTHETIC` |
| PNG and JPEG (scans, photos) | 003 seeds | A visible label band in the margin, plus a PNG `tEXt` chunk or JPEG comment `SYNTHETIC` |
| Plain-text and HTML notices and drafts | 001/006 | A first line or `<div role="note">` with `SYNTHETIC_LABEL` |

- `SYNTHETIC_LABEL` is `"SYNTHETIC – NOT A REAL DOCUMENT"`.
- `packages/platform/synthetic.py` holds the only functions that apply the marker (`stamp_pdf`, `stamp_image`, `stamp_text`) and the only checker (`is_marked`).
- The label is never placed over the document body, so the 002 extraction still reads the content.

## Settings

Defined by `packages/platform/settings.py` (`Settings`). Every field, its type, default and validation is listed in [contracts/settings.md](contracts/settings.md) (FR-000-03, FR-000-04, FR-000-12).

## Log record

The structlog JSON line. Its fields and masking rules are in [contracts/logging.md](contracts/logging.md) (FR-000-10, FR-000-11).

## Trace span (AI runs)

These are OpenTelemetry spans exported to Phoenix (FR-000-28). Only these attributes are allowed:
- `session.id` (= case_id), `workflow_id`, `agent`, `prompt.id`, `prompt.version`
- `llm.provider`, `llm.model_name`
- `llm.token_count.prompt`, `llm.token_count.completion`, `llm.token_count.total`
- `llm.cost.total_usd`
- span kind, duration, `tool.name`, `validation.outcome`, `citation.count`

Everything else is dropped by `MaskingSpanExporter` before export, including message content, input/output values and exception messages.

## Domain models summary (contracts PR, `packages/domain/`)

| Module | Models |
|---|---|
| `auth.py` | `Role`, `UserPublic`, `Principal`, `SystemCredentialClaims`, `LoginRequest`, `SessionInfo` |
| `audit.py` | `AuditLogEntry`, `AuditAction`, `ActorType`, `AuditOutcome` |
| `errors.py` | `ErrorEnvelope`, `ErrorBody`, `ErrorCode`, `FieldError` |
| `health.py` | `HealthReport`, `ReadinessReport`, `ReadinessCheck`, `ReadinessStatus`, `CheckStatus` |
| `dataset.py` | `DatasetMetadata` |
| `agent_run.py` | `AgentRunContext{case_id, workflow_id}`, `AgentRunUsage{model, provider, input_tokens, output_tokens, cost_usd, duration_ms, recorded}` |
