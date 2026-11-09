# Backend architecture (benefit-be)

All backend code lives in one repo and follows this layout. Put new code in the folder that owns it; don't create new top-level folders without updating this file.

```
api/
  apps/
    api/              FastAPI: REST endpoints, auth, starts workflows and sends Temporal signals
    worker/           Temporal worker process
      workflows/      CaseWorkflow, RenewalWorkflow (deterministic, no I/O)
      activities/     thin wrappers that call agents, the rules engine and the DB
  packages/
    agents/           LangGraph graphs + LangChain pieces (prompts, model client,
                      structured-output parsers, retrievers, MCP tool adapters)
    rules/            rules engine (pure Python)
    rag/              ingestion, Qwen3 embeddings, hybrid search
    mcp_servers/      case-mcp, docs-mcp, verify-mcp, policy-mcp
    domain/           shared Pydantic models used by everything above
    platform/         settings, logging, error format, auth helpers (no business logic)
  db/migrations/      Alembic
  analytics/          reporting / dbt models
  seed/               synthetic data generator (fixed seed); policy_manual/ holds the
                      training-edition manual
  evals/              evaluation sets and the evaluation command (002, 004)
  tests/              mirrors the source tree
Makefile, Procfile, .env.example   run commands (dev, prod, seed, eval) and settings
```

## Runtime processes

All four run from this repo:

| Process | Code | Role |
|---|---|---|
| FastAPI server | `apps/api/` | Handles UI requests, starts workflows, sends signals for caseworker actions |
| Temporal worker | `apps/worker/` | Runs workflows and their activities; activities call into `packages/agents` |
| MCP servers | `packages/mcp_servers/<name>/` | One small process each; agents connect through `langchain-mcp-adapters` |
| Temporal dev server | not our code | Installed with Homebrew, started by `make dev` in this repo |

## Rules

### Temporal (`apps/worker/`)
- Workflows are pure orchestration and must be deterministic: no I/O, network, DB, file access, `datetime.now()`, randomness or threads. Use Temporal's APIs (`workflow.now()`, timers, signals) instead.
- Activities are the only place that calls anything outside the workflow. Keep them thin: translate inputs, call one package function, return the result. No business logic in activities.
- Activity inputs and outputs are `packages/domain` Pydantic models.

### Agents (`packages/agents/`)
- LangChain provides the building blocks (model client, prompts, parsers, retrievers, MCP tools); LangGraph wires them into graphs. Both live here and nowhere else.
- Nothing in `packages/agents/` imports Temporal. Agents are plain async functions that take domain models and return a result.
- Agents reach external systems only through MCP tools (via `langchain-mcp-adapters`) or `packages/rag`. They don't open DB connections themselves.

### Other packages
- `packages/rules/` is pure Python: no I/O, no framework imports, fully unit-testable.
- `packages/domain/` holds shared Pydantic models only and imports nothing else from this repo.
- Each MCP server in `packages/mcp_servers/` is self-contained and runs as its own process.

### API (`apps/api/`)
- Talks to Temporal only to start workflows and send signals or queries. It never calls agents directly.
- Inside `apps/api/`, follow the `routers/ → services/ → repositories/` layering from [backend-python.md](backend-python.md).

### Dependency direction

```
apps/api  ─┐
           ├──>  packages/*  ──>  packages/domain
apps/worker┘
```

- `apps/*` may import `packages/*`. `packages/*` never import `apps/*`.
- Only `apps/worker/activities` imports `packages/agents`, `packages/rules` and `packages/rag`.
- `apps/api` and `apps/worker` don't import each other.

### Seed data and evaluations (`seed/`, `evals/`)
- Both are scripts and data, not runtime code: they may import `packages/*`, and nothing imports them.
- The generator in `seed/` is reproducible from a fixed seed. Everything it generates (households,
  documents and the expected-value test sets) goes to `seed/generated/`, which is git-ignored and
  rebuilt with `make seed`; the generator, the seed value and `seed/policy_manual/` are committed.
- `evals/` holds the committed question sets and the evaluation command. The command reads
  `seed/generated/` and the caseworker overrides stored at runtime. Evaluation runs call a live
  model and never run in CI.

### Database
- Schema changes only through Alembic migrations in `db/migrations/`. Never edit an applied migration; add a new one.

### Testing
- Agents: test without Temporal, with the model client and MCP tools faked.
- Workflows: test with Temporal's test environment and stubbed activities or agents.
- Rules: plain unit tests.
- Tests live in `tests/`, mirroring the source folder structure.

## Ownership

Workflows (`apps/worker/`, Lane A) and Agents (`packages/agents/`, Lane B) belong to different lanes. Whoever currently holds a lane makes its changes; people rotate between lanes (see the lane table in `specs/README.md`). Tests in `tests/` belong to the lane that owns the matching source folder. A change that needs both is split into separate commits per lane, and the shared contract goes through `packages/domain`.
