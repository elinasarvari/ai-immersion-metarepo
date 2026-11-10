# Quickstart validation: Platform Foundations (000)

These are runnable scenarios that prove 000 works from start to finish. Each one names the requirement or success criterion it proves. Commands and ports are in [contracts/commands-and-ci.md](contracts/commands-and-ci.md), settings in [contracts/settings.md](contracts/settings.md), and API shapes in [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml).

## Prerequisites

- An Apple-silicon Mac with Homebrew, and git access to `elinasarvari/benefit-be` and `elinasarvari/benefit-fe`. Both are public.
- Both repos cloned side by side, on `feature/000-platform-foundations` or `main` after merge:

  ```bash
  skills/clone-repo/clone-repo.sh https://github.com/elinasarvari/benefit-be.git
  skills/clone-repo/clone-repo.sh https://github.com/elinasarvari/benefit-fe.git
  cd repos/benefit-be
  ```

- For scenario 6 only: an Anthropic API key, or Bedrock access (region and inference-profile ID).

## 1. From a fresh clone to a healthy system (US1; FR-000-01, FR-000-03; SC-000-01)

Time this scenario. It must finish in **under 30 minutes**.

```bash
make doctor          # lists any missing tool; install with the next line
make setup           # brew bundle, uv sync, pnpm install, .env with generated secrets, make mongo-up
make reset           # migrate, seed, write the synthetic marker
make dev             # leave running in terminal A
```

In terminal B:

```bash
make health
```

**Expected:**
- `make health` prints a table where the api, worker, temporal, phoenix and web rows all show `ready`, then exits 0.
- `http://localhost:5173` shows the sign-in page with the SYNTHETIC banner.
- `git status` is clean: `.env` and `.data/` are ignored, and `.env.example` is committed.

Then stop `make dev`, run `make prod`, and run `make health` again.

**Expected:** all components are `ready`. The API runs without reload, the web runs from `vite preview` on 5173, and the session cookie is `Secure` only when `WEB_ORIGIN` is https (the local profile is plain http, and browsers such as Safari refuse `Secure` cookies on http).

## 2. Reset reloads synthetic data (US1 scenario 3; FR-000-02, FR-000-14)

With `make dev` running:

```bash
make reset && make health
mongosh "$MONGO_URL_OWNER" --quiet --eval 'db.getSiblingDB("benefit")._meta.findOne()'
```

**Expected:**
- Seeded counts are restored.
- MongoDB shows `{_id:"dataset", synthetic:true}`, and the DuckDB marker model passes its dbt test.
- `temporal workflow list --query 'ExecutionStatus="Running"'` is empty.
- The `benefit` project in Phoenix is empty.
- `make health` is green again.
- `uv run pytest -m integration -k FR_000_14_every_generated_document_is_marked` passes.
- Opening the sample pay stub in `db/seeds/generated/` shows the SYNTHETIC label band at the top and bottom of the page, clear of the pay details.

## 3. Missing or invalid settings refuse to start (FR-000-04; US4 scenario 3)

```bash
LLM_PROVIDER=openai uv run python -m apps.worker.main; echo "exit=$?"
env -u SESSION_SECRET uv run uvicorn apps.api.main:create_app --factory; echo "exit=$?"
```

**Expected:**
- `exit=2`, with a line naming the setting: `setting LLM_PROVIDER: invalid value; allowed: anthropic, bedrock`, and `setting SESSION_SECRET: …` for the second command.
- No setting values are printed.

## 4. Sign in with a role; protected calls refused without a session (US2; FR-000-05–07, FR-000-21, FR-000-23; SC-000-02)

```bash
source .env
curl -si -c /tmp/cw.txt -H 'content-type: application/json' \
  -d "{\"username\":\"caseworker1\",\"password\":\"$DEMO_PASSWORD\"}" \
  localhost:8000/api/v1/auth/login                     # 200, Set-Cookie benefit_session (HttpOnly)
curl -s -b /tmp/cw.txt localhost:8000/api/v1/auth/me   # role: caseworker, expires_at ≈ now + 8h
curl -s localhost:8000/api/v1/auth/me                  # 401 {"error":{"code":"auth.required",…}}
curl -s -H 'content-type: application/json' -d '{"username":"caseworker1","password":"wrong"}' \
  localhost:8000/api/v1/auth/login                     # 401 auth.invalid_credentials
```

Then check the audit log:

```bash
mongosh "$MONGO_URL_OWNER" --quiet --eval 'db.getSiblingDB("benefit").audit_log.find({}, {action:1,outcome:1,actor_type:1,_id:0}).sort({_id:-1}).limit(2)'
```

**Expected:**
- The two most recent rows are `sign_in failure anonymous` and `sign_in success user`.
- No username or password appears in any audit column or log line.

**Session expiry:** restart the API with `SESSION_TTL_HOURS=1`, and replay a token with `exp` in the past (the unit tests use `FixedClock`). The API returns `401 auth.session_expired`, and the SPA redirects to `/sign-in?reason=expired`.

**Coverage of every route:** `make test-contract` runs `test_every_route_protected`, which walks every route and expects 401 without a session (SC-000-02).

**In the browser:**
- Sign in as each of `applicant1`, `caseworker1` and `supervisor1`. Each lands in their own area.
- An applicant who opens `/caseworker` is redirected to the forbidden page.

## 5. Structured errors trace to a log line (US3; FR-000-08, FR-000-10, FR-000-11; SC-000-05)

```bash
curl -si -H 'content-type: application/json' -d '{}' localhost:8000/api/v1/auth/login
```

**Expected:** `422` with `error.code = validation_failed`, `fields` naming `body.username` and `body.password`, a `reference_id`, and an `X-Request-ID` header with the same value.

For an internal error:

```bash
make test-api   # includes test_FR_000_08_unexpected_error_returns_generic_message_with_reference
```

**Expected:**
- The client sees a generic message and a reference ID, with no stack trace, SQL or host.
- Searching the API log output for that reference ID finds one line, with the stack trace, **in under a minute**.
- No synthetic name, date of birth or SSN-like value appears in the logs (`test_FR_000_11_*`).

## 6. Switch AI provider by configuration (US4; FR-000-12, FR-000-13; SC-000-04)

```bash
LLM_PROVIDER=anthropic make smoke-ai     # needs ANTHROPIC_API_KEY
LLM_PROVIDER=bedrock   make smoke-ai     # needs AWS_REGION, BEDROCK_MODEL_ID and AWS credentials
```

**Expected:**
- Both pass the same five checks: plain call, cited structured output, PDF field extraction, tool binding, and usage/cost recorded.
- No code changes between the two runs.
- Each run appears in Phoenix (`http://localhost:6006`) with the provider, model, tokens and cost.

## 7. Health versus readiness when a dependency is down (US3 scenario 3; edge case; FR-000-09, FR-000-28)

```bash
make mongo-down
curl -s localhost:8000/api/v1/health       # 200 status ok
curl -s -w '%{http_code}\n' localhost:8000/api/v1/ready   # 503 not_ready, check mongo: down
make mongo-up
```

Then stop only the `phoenix` process and check `/ready` again.

**Expected:** `200 degraded` with `tracing: degraded`. AI runs, for example the fake-mode tests, still pass.

## 8. Tracing has no personal data and can be found by case (FR-000-28; SC-000-09)

```bash
make test-unit -- -k FR_000_28   # spans tagged with case and workflow; exported spans contain no planted personal data
```

**Expected:** all tests pass. With `make dev` running in `LLM_MODE=recorded`, a demo case's agent run can be found in Phoenix by searching for its case ID (session ID).

## 9. Quality gates on every PR (US5; FR-000-16–20, FR-000-24–26; SC-000-03, SC-000-06, SC-000-08)

Locally:

```bash
make check                                    # ruff, mypy --strict, unit, workflow, contract, openapi-check, gitleaks, pip-audit
(cd ../benefit-fe && pnpm lint && pnpm typecheck && pnpm test && pnpm api:check)
make e2e                                      # sign-in spec passes; six journeys show as "pending (fixme)"
```

In CI, open a throwaway draft PR in benefit-be that contains:
1. a ruff error
2. a failing unit test
3. a route change without regenerating `openapi/openapi.json`

**Expected:**
- `static`, `unit` and `contract` fail. `contract` names the changed path.
- The PR shows every job.
- Merging is blocked once 009's branch protection is in place.
- The `e2e` job's summary shows that benefit-fe ran on the same-named branch if it exists, otherwise `main`.
- A green run takes **under 15 minutes**. If it doesn't, switch on the `@smoke` fallback from research R25.
- Gitleaks finds nothing in either repo.

## 10. Time zone (FR-000-27)

```bash
make test-unit -- -k FR_000_27
```

**Expected:** 05:30 UTC on a given day is counted as the previous Chicago day, and the DST boundaries are counted correctly. The same tests pass on CI (Linux) and on macOS.
