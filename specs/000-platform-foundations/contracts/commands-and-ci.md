# Contract: commands, processes and CI checks

This is what a developer and CI can rely on. The commands live in `benefit-be` (constitution IX, PL-12–PL-14), except where marked `benefit-fe`.

## Make targets (benefit-be)

| Target | Does | Exit code |
|---|---|---|
| `make doctor` | Checks the Brewfile tools and versions: python@3.12, uv, node 24, pnpm, mongodb-community@8.0, mongosh, temporal, gitleaks. Also checks that `.env` exists and that `BENEFIT_FE_DIR` is a checkout. | non-zero, listing what is missing |
| `make setup` | `brew bundle`, `uv sync --frozen`, `pnpm --dir $BENEFIT_FE_DIR install --frozen-lockfile`, `pre-commit install`, then `make mongo-up`. Creates `.env` with generated secrets (including the two MongoDB passwords and the keyfile) if it is missing. | |
| `make mongo-up` | Starts `mongod` forked in the background as a single-node replica set (`rs0`) with authentication, data in `.data/mongo`. On the first run it initiates the replica set and creates the `benefit_owner` and `benefit_app` users and the `auditAppend` role (`db/mongo/provision.py`). Safe to run when it is already up. | non-zero if it can't start |
| `make mongo-down` | Stops that `mongod` | |
| `make dev` | `honcho -f Procfile start`: every process in development mode (FR-000-01) | |
| `make prod` | Builds the frontend, then `honcho -f Procfile.prod start` with `APP_ENV=prod` (FR-000-01) | |
| `make seed` | Runs the fixed-seed generator. Output goes to `db/seeds/generated/`. | |
| `make reset` | Clears all data and reloads the synthetic data set while the system is running (FR-000-02, R13): migrations down to base and up to head (collections, validators, indexes), DuckDB rebuilt from the Mongo export, seed run, marker written, running Temporal workflows terminated, Phoenix project deleted. | non-zero if the safety guard refuses |
| `make health` | Polls every component's health and readiness and prints a table | 0 only if every component is `ready` or `degraded` |
| `make smoke-ai` | Runs the live AI smoke test (`pytest -m live_llm`) with the current `LLM_PROVIDER`, forcing `LLM_MODE=live`. Never run in CI. | |
| `make openapi` | Regenerates `openapi/openapi.json` | |
| `make openapi-check` | Regenerates the file, then `git diff --exit-code openapi/openapi.json` | non-zero on drift |
| `make lint` | `ruff check` and `ruff format --check` | |
| `make typecheck` | `mypy --strict` | |
| `make test-unit` / `test-workflow` / `test-contract` / `test-integration` | `pytest -m <level> $(PYTEST_ARGS)`. Integration tests need MongoDB (`make mongo-up`) and Temporal. | |
| `make test-api` / `make test-stack` | `pytest -m api` / `pytest -m stack` against a running stack (`make dev`, or `Procfile.ci` in CI) | |
| `make test` | Every level that needs no running stack (excludes `api`, `stack` and `live_llm`) | |
| `make check` | lint, typecheck, test-unit, test-workflow, test-contract, openapi-check, `gitleaks detect`, `pip-audit` (PL-14, PR-6) | |
| `make e2e` | `pnpm --dir $BENEFIT_FE_DIR e2e` against the running stack | |

## Scripts (benefit-fe `package.json`)

| Script | Does |
|---|---|
| `dev` / `build` / `preview` | Vite |
| `lint` / `format:check` / `typecheck` | ESLint, Prettier, `tsc --noEmit` |
| `test` | Vitest |
| `api:gen` | Fetches `openapi/openapi.json` at the commit in `openapi/BE_COMMIT`, then generates `src/api/generated/schema.d.ts` with openapi-typescript |
| `api:check` | Runs `api:gen`, then fails on any diff (FR-000-26) |
| `e2e` | `playwright test` (Chromium). `e2e:all` runs every browser. |

## Processes and ports

| Process | Procfile | Procfile.prod | Procfile.ci | Port | Health / ready |
|---|---|---|---|---|---|
| MongoDB 8.0 (replica set `rs0`) | `make mongo-up` | `make mongo-up` | `make mongo-up` (apt `mongodb-org` 8.0) | 27017 | readiness probes |
| `temporal` | ✓ | ✓ | ✓ | 7233 (UI 8233) | `temporal operator cluster health` |
| `api` | ✓ (reload) | ✓ | ✓ | 8000 | `/api/v1/health`, `/api/v1/ready` |
| `worker` | ✓ | ✓ | ✓ | 8001 | `/health`, `/ready` |
| `phoenix` | ✓ | ✓ | — | 6006 | `GET /healthz` |
| `web` | `pnpm dev` | `pnpm preview` | `pnpm preview` | 5173 (preview is pinned to the same port) | HTTP 200 on `/` |
| MCP servers (005) | ✓ | ✓ | ✓ | 8101–8104 | `/health`, `/ready` |

## Required CI checks (both repos, every PR and every push to `main` or `feature/**`; FR-000-16)

| Job | benefit-be | benefit-fe |
|---|---|---|
| `static` | ruff, `mypy --strict`, `pip-audit`, gitleaks | ESLint, Prettier, `tsc --noEmit`, `pnpm audit --audit-level high`, gitleaks |
| `unit` | `pytest -m unit` | Vitest |
| `workflow` | `pytest -m workflow` (time-skipping, replay, restart) | n/a |
| `contract` | `openapi-check`, `pytest -m contract` (OpenAPI paths, tool schemas) | `api:check`, plus the vendored spec compared with benefit-be's same-named branch, otherwise `main` |
| `integration` | `pytest -m integration` against MongoDB from `make mongo-up` and the Temporal CLI, after `make reset` | n/a |
| `e2e` | Checks out benefit-fe at the same-named branch, otherwise `main` (FR-000-25), starts `Procfile.ci`, runs `pytest -m "stack or api"`, then Playwright | Checks out benefit-be the same way, starts its `Procfile.ci`, runs Playwright |

CI environment: `APP_ENV=test`, `LLM_MODE=fake`, `EMBEDDER=fake`, `RERANKER=fake`, `TRACING_ENABLED=false`, and a random `DEMO_PASSWORD` per run. No AI credentials are present (FR-000-20, PR-5).

Merge blocking: branch protection makes every job above required. It is configured by 009 (FR-009-02).

## Pending end-to-end journeys (FR-000-19)

Each journey has a spec file in `benefit-fe/e2e/` from the start, marked `test.fixme()` with the annotation `{ type: 'pending', description: '<FR ids>; built by <feature>' }`. The feature that builds the journey replaces `fixme` with `test`.

| Spec file | Journey | Built by |
|---|---|---|
| `mismatch-request-info.spec.ts` | Mismatch and request for information | 002, 001 |
| `restart-resume.spec.ts` | Restart and resume | 001 |
| `missed-deadline-override.spec.ts` | Missed deadline and override | 001, 006 |
| `automatic-renewal.spec.ts` | Automatic renewal | 007 |
| `renewal-one-document.spec.ts` | Renewal needing one document | 007 |
| `applicant-blocked-other-household.spec.ts` | An applicant blocked from another household's records | 006, 005 |
