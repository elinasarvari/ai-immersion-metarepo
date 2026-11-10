# Rule sets

These are the rules generated code must pass. Spec Kit plans are written against them, `/speckit-implement` follows them, and the compliance review (`agents/compliance-reviewer/`) checks the result against them before a PR is opened.

Every rule has an ID (for example `TW-3`). Reviews cite the ID, the file and the line.

## Which rules apply where

| Repo | Path | Lane (owner) | Rule sets |
|---|---|---|---|
| benefit-be | `apps/worker/` | Workflows | [temporal-workflows.md](temporal-workflows.md) |
| benefit-be | `packages/agents/`, `evals/` (extraction, explanations, agent success) | Agents | [agents-llm.md](agents-llm.md) |
| benefit-be | `packages/rag/`, `packages/rules/`, `db/`, `analytics/`, `data/policy/`, `evals/` (retrieval) | Knowledge & data | [data-knowledge.md](data-knowledge.md), [database.md](database.md) |
| benefit-be | `apps/api/`, `packages/mcp_servers/`, `packages/platform/`, Makefile, Procfile, setup | Platform & UI | [platform-api.md](platform-api.md), [api-generation.md](api-generation.md) |
| benefit-be | `packages/domain/` | Shared (all lanes agree) | [backend-architecture.md](backend-architecture.md) |
| benefit-fe | everything | Platform & UI | [frontend-ui.md](frontend-ui.md), [frontend-react.md](frontend-react.md) |

These apply everywhere, in both repos:
- [backend-architecture.md](backend-architecture.md) (`BA-*`): backend layout and import boundaries
- [backend-python.md](backend-python.md): Python basics
- [security.md](security.md) and [testing.md](testing.md)

## Precedence

When two files disagree, the more specific one wins:
1. The lane file (for example `temporal-workflows.md`)
2. `backend-architecture.md` or `frontend-ui.md`
3. The general files (`backend-python.md`, `frontend-react.md`, `database.md`, `api-generation.md`, `security.md`, `testing.md`)

## Project-wide rules (`PR-*`)

- **PR-1** Rules decide eligibility; AI only assists. No AI output may set a determination directly.
- **PR-2** Every AI output cites its source: a document field or a policy chunk ID.
- **PR-3** Synthetic data only. No real personal data in code, tests, fixtures, seeds, evals, logs or prompts.
- **PR-4** All package versions are pinned, and lockfiles (`uv.lock`, `pnpm-lock.yaml`) are committed with any dependency change.
- **PR-5** Everything runs natively on a Mac: no Docker, no cloud services. CI runs on GitHub-hosted runners and may use service containers there (FR-000-24); nothing else does. The only network calls are to Claude, through the Anthropic API or Amazon Bedrock (chosen by `LLM_PROVIDER`).
- **PR-6** `make check` passes before a PR is opened. Changes to agents, retrieval or extraction also pass `make eval` thresholds.
