# Handoff: planning session to build sessions (2026-11-09)

Context for a new Claude Code session started in this repo. Start by reading this file, then
`specs/README.md` and `.specify/memory/constitution.md`.

## Where things stand

- Branch `feature/initial-specs`: constitution v1.4.1 and specs 000–009, merged with `main`
  (PR #1 lane rules and agents). PR #3 to `main` opened for team review.
- The merge with `main` (`eb03330`) truncated every spec; `f376694` restored them.
- A second completeness review added feature 009 (delivery factory and demo readiness) and closed
  gaps in 000–008 with defaults. The team confirms or overrules them in PR review: see "Spec
  review round 2" in `specs/README.md`.
- The team pages (pitch, tech stack, build process) predate round 2: they still show specs
  000–008, constitution v1.3.0, a policy filter by date and "8–10 rules" (the spec has 6).
- PR #2 (`feature/project-rules`) changes `project-rules/testing.md`; check its test naming
  against constitution Principle V (`test_FR_NNN_nn_...`) before merging.
- Not started: submodules `repos/benefit-be` and `repos/benefit-fe` (README still has `OWNER`
  placeholders), `/speckit-plan` for any feature, the Day 1 contracts PR.

## Team pages (shared with the organization)

| Page | Link |
|---|---|
| Project hub (start here) | https://claude.ai/artifact/Vmy8w3CJ71TiUp1Jo8PTUo |
| Pitch (business case) | https://claude.ai/artifact/TK6m62sWqr4x7Aq9xgkXtL |
| Tech stack | https://claude.ai/artifact/RFDMwFwTeycpJwNTsXHmow |
| Build process | https://claude.ai/artifact/FgFY6qkFterpo8Q2YrDvfR |

To update a page from a new session: read it by URL with the Artifact tool, edit, and republish
to the same URL. The original local files were in the old session's temporary folder.

## Decisions to keep in mind

Most decisions are recorded in `specs/README.md`, the constitution and `project-rules/`.
These are the ones a new session is most likely to get wrong:

- **Keep it simple.** 3 people, 3 days. Prefer the simplest option that meets the specs;
  propose cuts from the "Cut first if behind" list rather than adding tools or features.
- **Scope:** Illinois Medicaid, adults 19–64 on income; new applications, redeterminations,
  applicant self-service, human review, program metrics. All data synthetic, treated as real.
- **Required technologies:** Temporal, LangGraph, LangChain, RAG, MCP, PostgreSQL + pgvector,
  MongoDB, DuckDB + dbt. Local only: native installs on Macs, no Docker, nothing deployed.
- **AI provider:** Claude Opus 5.5 via the Anthropic API or Amazon Bedrock (one teammate has
  only Bedrock), switched by `LLM_PROVIDER` in one factory. Evaluation scores are recorded
  against the Anthropic API. CI never calls a live model.
- **Lanes:** four lanes from `project-rules/README.md` (Workflows, Agents, Knowledge & data,
  Platform & UI). Three people rotate between seats: Workflows + Agents, Knowledge & data,
  Platform & UI. Who is Person 1, 2 and 3 is not yet decided.
- **Folder names:** main's layout in `project-rules/backend-architecture.md` (paths from the
  `benefit-be` root; `db/seeds/`, `data/policy/`, `evals/`, `packages/platform/`).
- **Human review:** caseworkers approve adverse outcomes and AI-drafted or adverse notices;
  favourable template notices go out directly. One shared review queue; reminder at 2 days,
  escalation flag at 4. Coverage never ends automatically.
- **Demo:** about 3 minutes, using the demo time scale (1 day = 1 minute) and the supervisor
  "advance clock" action. Journeys are listed in FR-000-19.

## Next steps

1. Team reviews the PR; merge to `main`.
2. Add the submodules with `skills/clone-repo/clone-repo.sh <url>` and fix the README `OWNER`
   placeholders.
3. Decide who starts as Person 1, 2 and 3 (rotation table in `specs/README.md`).
4. Day 1 morning: the contracts PR (outline in `specs/README.md`), then `/speckit-plan` for
   000, 001, 003 and 005 with `SPECIFY_FEATURE_DIRECTORY=specs/<NNN-feature>` set.
