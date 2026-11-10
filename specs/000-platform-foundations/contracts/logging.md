# Contract: structured logs

These rules apply to every `benefit-be` process (API, worker, MCP servers, seeds and scripts). Logging is set up once in `packages/platform/logging.py` (FR-000-10, FR-000-11, PL-11, R10).

## Output

- One JSON object per line on stdout. honcho prefixes each line with the process name.
- Standard-library `logging`, uvicorn, `temporalio` and `httpx` logs go through the same structlog processor chain.

## Fields

| Field | Always | Meaning |
|---|---|---|
| `timestamp` | yes | ISO 8601 in UTC |
| `level` | yes | `debug` … `critical` |
| `event` | yes | A short constant message, e.g. `request.completed` or `auth.sign_in.failed` |
| `component` | yes | `api`, `worker`, `mcp.<name>`, `seed` |
| `request_id` | when known | The request reference ID. It matches `X-Request-ID`, `error.reference_id` and `audit_log.reference_id`. |
| `case_id` | when known | Bound by the route or the activity interceptor |
| `workflow_id`, `run_id` | when known | Bound by the worker interceptor and by the API when it starts or signals a workflow |
| `activity_type`, `attempt` | in activities | |
| `user_id`, `role` | when signed in | A UUID, never a username |
| `method`, `route`, `status`, `duration_ms` | `request.completed` | `route` is the route template (`/api/v1/cases/{case_id}`), not the raw path |
| `error_code` | on errors | An `ErrorCode` value |
| `exception` | on 5xx | Stack trace, after masking. **Only in logs**, never in a response. |

## How `request_id` travels

1. The SPA or another client may send `X-Request-ID` (a UUID). If it is missing or invalid, the API generates a `uuid4`.
2. The API middleware binds it to the log context and returns it in the response header.
3. When the API starts or signals a workflow, a Temporal client interceptor sets the header `x-request-id`.
4. A worker activity inbound interceptor reads that header and binds it, together with `workflow_id` and `case_id`.

## Masking (`mask_pii` processor)

Masking runs last before rendering. Masked values become `"***"`.

**By key** (case-insensitive, at any nesting depth): `name`, `first_name`, `last_name`, `full_name`, `display_name`, `username`, `address`, `street`, `city`, `zip`, `dob`, `date_of_birth`, `birth_date`, `ssn`, `identity_number`, `id_number`, `document_text`, `text`, `content`, `body`, `password`, `password_hash`, `token`, `tool_credential`, `authorization`, `cookie`, `set-cookie`, `api_key`, `secret`.

**By pattern** (any string value, including exception text):
- SSN-like numbers: `\b\d{3}-?\d{2}-?\d{4}\b`
- ISO dates within a key path containing `birth`
- JWT-like strings: `eyJ[\w-]+\.[\w-]+\.[\w-]+`

**Never logged at all:** request and response bodies, raw query strings, SQL parameters, model prompts and completions, and document bytes.

## Test hooks

`tests/packages/platform/test_logging.py` plants synthetic personal data under each masked key and pattern, then asserts that the rendered line contains none of it (FR-000-11). The worker and API have matching tests that check a token never appears in the logs (FR-000-22).
