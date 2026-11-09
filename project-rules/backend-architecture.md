# Backend architecture: benefit-be (`BA-*`)

All backend code lives in the `benefit-be` repo and follows this layout. The UI is a separate repo, `benefit-fe` (see [frontend-ui.md](frontend-ui.md)). Lane-specific rules are in the files listed in [README.md](README.md).

```
benefit-be/
  apps/
    api/              FastAPI: REST endpoints (/api/v1), auth, starts workflows and sends Temporal signals
    worker/           Temporal worker process
      workflows/      CaseWorkflow, RenewalWorkflow (deterministic, no I/O)
      activities/     thin wrappers that call agents, the rules engine and the DB
  packages/
    agents/           LangGraph graphs + LangChain pieces (prompts, model client,
                      structured-output parsers, retrievers, MCP tool adapters)
    rules/            rules engine (pure Python)
    rag/              ingestion, Qwen3 embeddings, hybrid search, reranking
    mcp_servers/      case-mcp, docs-mcp, verify-mcp, policy-mcp
    domain/           shared Pydantic models used by everything above
  db/
    migrations/       Alembic
    seeds/            synthetic data only
  evals/              retrieval, extraction and agent-success evals (make eval)
  analytics/          dbt models (DuckDB)
  data/policy/        policy source documents
  tests/
  Brewfile  Procfile  Makefile  pyproject.toml  uv.lock  .env.example
```

## Runtime processes

All run from `benefit-be`, started together by `make dev` (Procfile and `honcho`):

| Process | Code | Role |
|---|---|---|
| FastAPI server | `apps/api/` | Handles UI requests, starts workflows, sends signals for caseworker actions |
| Temporal worker | `apps/worker/` | Runs workflows and their activities; activities call into `packages/agents` |
| MCP servers | `packages/mcp_servers/<name>/` | One small process each; agents connect through `langchain-mcp-adapters` |
| Temporal dev server | not our code | Installed with Homebrew, started by `make dev` |
| Arize Phoenix | not our code | Local LLM tracing |

## Rules

### Layout
- **BA-1** New code goes in the folder that owns it, as shown above. Don't create new top-level folders or packages without updating this file.
- **BA-2** Inside `apps/api/`, follow the `routers/ → services/ → repositories/` layering from [backend-python.md](backend-python.md).

### Dependency direction

```
apps/api  ──┐
            ├──>  packages/*  ──>  packages/domain
apps/worker ┘
```

- **BA-3** `apps/*` may import `packages/*`. `packages/*` never import `apps/*`.
- **BA-4** Only `apps/worker/activities/` imports `packages/agents`, `packages/rules` and `packages/rag`.
- **BA-5** `apps/api` and `apps/worker` don't import each other. They communicate through Temporal.
- **BA-6** `packages/domain` holds shared Pydantic models only and imports nothing else from this repo.
- **BA-7** Nothing outside `apps/worker/` imports `temporalio`, except `apps/api`, which uses the Temporal client to start workflows and send signals.

### Contracts
- **BA-8** Data passed between lanes (activity inputs and outputs, signal payloads, agent results) is defined in `packages/domain`. Changing it needs agreement from every lane that uses it, and the PR says so.

### Testing
- **BA-9** Tests live in `tests/`, mirroring the source folder structure. Integration tests run against local Postgres and MongoDB.

## Ownership

| Lane | Owns |
|---|---|
| Workflows | `apps/worker/` |
| Agents | `packages/agents/`, extraction evals |
| Knowledge & data | `packages/rag/`, `packages/rules/`, `db/`, `analytics/`, `data/policy/`, retrieval evals |
| Platform & UI | `apps/api/`, `packages/mcp_servers/`, Makefile and setup, plus the `benefit-fe` repo |

Changes that need more than one lane are split so each lane's files change in their own commits, and the shared contract goes through `packages/domain` (`BA-8`).
