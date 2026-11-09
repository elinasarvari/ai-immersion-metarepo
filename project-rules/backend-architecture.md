# Backend architecture: benefit-be (`BA-*`)

All backend code lives in the `benefit-be` repo and follows this layout. The UI is a separate repo, `benefit-fe` (see [frontend-ui.md](frontend-ui.md)). Lane-specific rules are in the files listed in [README.md](README.md).

```
benefit-be/
  apps/
    api/              FastAPI: REST endpoints (/api/v1), auth, starts workflows and sends Temporal signals
    worker/           Temporal worker process
      workflows/      CaseWorkflow for applications and redeterminations (deterministic, no I/O)
      activities/     thin wrappers that call agents, the rules engine and the DB
  packages/
    agents/           LangGraph graphs + LangChain pieces (prompts, model client,
                      structured-output parsers, retrievers, MCP tool adapters)
    rules/            rules engine (pure Python)
    rag/              ingestion, Qwen3 embeddings, hybrid search, reranking
    mcp_servers/      case-mcp, docs-mcp, verify-mcp, policy-mcp
    domain/           shared Pydantic models used by everything above
    platform/         settings, logging, error format, auth helpers (no business logic)
  db/
    migrations/       Alembic
    seeds/            synthetic data generator (fixed seed); output in generated/ (git-ignored)
  evals/              retrieval, extraction, explanation and agent-success evals (make eval)
  analytics/          dbt models (DuckDB)
  data/policy/        training-edition policy manual (written by the team)
  tests/              mirrors the source tree
  Brewfile  Procfile  Makefile  pyproject.toml  uv.lock  .env.example
```

## Runtime processes

All run from `benefit-be`, started together by `make dev` (Procfile and `honcho`). `make prod` starts the same processes with production settings.

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

### Seed data and evaluations
- **BA-10** `db/seeds/` and `evals/` are scripts and data, not runtime code: they may import `packages/*`, and nothing imports them.
- **BA-11** The seed generator is reproducible from a fixed seed. Everything it generates (households, documents and the expected-value test sets) goes to `db/seeds/generated/`, which is git-ignored and rebuilt with `make seed`. The generator, the seed value and `data/policy/` are committed.
- **BA-12** `evals/` holds the committed question sets and the evaluation command. The command reads `db/seeds/generated/` and the caseworker overrides stored at runtime. Evaluation runs call a live model and never run in CI.

## Ownership

| Lane | Owns |
|---|---|
| Workflows | `apps/worker/` |
| Agents | `packages/agents/`, extraction, explanation and agent-success evals |
| Knowledge & data | `packages/rag/`, `packages/rules/`, `db/` (including the baseline migration and `db/seeds/`), `analytics/`, `data/policy/`, retrieval evals |
| Platform & UI | `apps/api/`, `packages/mcp_servers/`, `packages/platform/`, Makefile, Procfile and setup, plus the `benefit-fe` repo |

Whoever currently holds a lane makes its changes; the three team members rotate between the four lanes (see `specs/README.md`). Tests in `tests/` belong to the lane that owns the matching source folder. Changes that need more than one lane are split so each lane's files change in their own commits, and the shared contract goes through `packages/domain` (`BA-8`).
