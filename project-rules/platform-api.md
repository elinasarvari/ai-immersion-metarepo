# Platform lane: API, MCP servers and operations (`PL-*`)

Applies to `benefit-be/apps/api/`, `packages/mcp_servers/`, `Makefile`, `Procfile`, `Brewfile` and `scripts/`. Owner: Platform & UI. [api-generation.md](api-generation.md) also applies.

## API (`apps/api/`)
- **PL-1** FastAPI with Pydantic v2. All routes are under `/api/v1`. Request and response bodies are `packages/domain` models or API-specific Pydantic models.
- **PL-2** The API starts workflows and sends signals or queries to Temporal. It never calls agents, the rules engine or RAG directly.
- **PL-3** The OpenAPI spec is the contract with `benefit-fe`. Any change to it is called out in the PR and paired with a `benefit-fe` PR that regenerates the client.
- **PL-4** Breaking API changes need a new version path, not an in-place change.

## Auth (both the API and MCP servers)
- **PL-5** JWT via `PyJWT`, with the roles `applicant`, `caseworker` and `supervisor`.
- **PL-6** Every API route and every MCP tool checks the caller's role and their access to the specific case. Applicants only see their own cases. MCP tools accept only the case-scoped system credential issued by the worker (FR-000-22), never a user session.
- **PL-7** Every route and tool has a test proving that each role it should reject is rejected.

## MCP servers (`packages/mcp_servers/`)
- **PL-8** Built with the official `mcp` Python SDK (FastMCP). Each server is its own process with its own entry in the `Procfile`.
- **PL-9** Each server owns one area: `case-mcp` (Postgres), `docs-mcp` (MongoDB and local files), `verify-mcp` (mocked income and identity checks) and `policy-mcp` (hybrid search and reranking).
- **PL-10** Tool inputs and outputs are typed Pydantic models with clear descriptions, because the agents read them.

## Logging and operations
- **PL-11** `structlog` JSON logs that include `case_id` and `workflow_id` wherever they exist. No personal data in logs.
- **PL-12** Every process starts through the `Procfile` and `honcho`. New processes are added there and to `make dev`.
- **PL-13** New tools go into the `Brewfile` or `pyproject.toml` (pinned), and `make doctor` checks for them.
- **PL-14** `make check` runs `ruff`, `mypy --strict`, `pytest`, `gitleaks` and `pip-audit`. Don't bypass `pre-commit`.
