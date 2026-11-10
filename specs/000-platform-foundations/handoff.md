# Handoff: 000 Platform foundations (2026-11-09, implementation session)

## State

Everything below runs locally and is verified by tests. Work is committed locally on `feature/000-platform-foundations` in both repos (benefit-be: lane-split commits plus two review-fix commits; benefit-fe: a feature commit plus a review-fix commit). Nothing is pushed, and the metarepo changes (specs, project-rules, constitution draft) are uncommitted. The PRs (`create-pr` skill) are still to do. All six reviewers (backend, frontend and the four lane agents) ran; their blocking findings are fixed.

- **benefit-be**: settings with fail-fast start-up, structured errors, request IDs, health and readiness, structured logging with PII masking, sign-in (argon2id, JWT cookie, roles), the audit log, household scoping, MongoDB provisioning, migrations and seeds, `make reset`, the Temporal worker with the smoke workflow, the case-scoped agent credential, interceptors, the fake embedder and reranker, contract tests, and CI workflows.
- **benefit-fe**: pnpm, strict TypeScript, ESLint and Prettier, Tailwind, the app shell and SYNTHETIC banner, sign-in and role guards, the generated API client, Playwright harness (18 tests pass against the live stack, 6 journeys pending), and CI workflows.
- **Agents lane** (`packages/agents/`): provider factory, replay model, tracing, live smoke test. See the agent report in the session summary.

The database is **MongoDB only** (draft constitution 2.0.0, research R27). `.specify/memory/constitution.md` carries the draft banner until all three of you approve it.

## Open items

| # | Item | Needs |
|---|---|---|
| P1 | Bedrock inference-profile ID and region | The person with Bedrock access. Blocks only `make smoke-ai` on Bedrock (T147 / V4). |
| P2 | Branch protection with the CI job names as required checks in both repos | A repo admin, through 009 |
| P3 | Tick the 000 items under "Spec review round 2" in `specs/README.md` | All three of you, in the contracts PR review |
| P4 | Order of the contracts PR and the 000 sign-in work | The team |
| P5 | Approve the draft constitution amendment 2.0.0 (MongoDB only) | All three of you, by PR |
| V1 | Phoenix `DELETE /v1/projects/{name}` was not verified (Phoenix is not installed here). `make reset` warns and carries on if it fails. | Run `make dev` with Phoenix once |
| V4 | Provider structured output on Anthropic and Bedrock | API keys |

## CI on GitHub (2026-11-09)

- Both branches are pushed, and the PRs are open: elinasarvari/benefit-be#1 and elinasarvari/benefit-fe#1. CI also runs on pushes to `feature/**`, so it runs without a PR.
- benefit-be: all 6 jobs green in 2m50s. benefit-fe: all 4 jobs green in 1m25s (SC-000-08: under 15 minutes).
- Gate check (T120): a throwaway benefit-be branch with a lint error, a failing test and an undocumented route failed `static`, `unit` and `contract` as intended. The branch is deleted.
- Merge the two PRs together. Until benefit-fe's PR merges, any benefit-be branch without a same-named benefit-fe branch fails `e2e`, because benefit-fe `main` is still the old npm scaffold (and the same in reverse).
- `benefit-fe/openapi/BE_COMMIT` is pinned to a real benefit-be commit.
- Local loop: `make verify` (every CI check, both repos) and `make mutation-audit` (22 planted bugs, all caught).

## Decisions worth knowing

- The audit log lives in its own database (`benefit_audit`) because MongoDB can't grant `readWrite` while excluding one collection. The runtime user has insert and find only.
- The first MongoDB user must hold only `userAdminAnyDatabase` (localhost exception); `provision.py` grants the rest afterwards.
- Integration tests use `benefit_test` and `benefit_audit_test`, never the development data.
- ESLint is pinned to 9.39.5 because `eslint-plugin-jsx-a11y` doesn't support ESLint 10.
- The session cookie is `Secure` only when `WEB_ORIGIN` is https.
- Homebrew pulled Node 26 in as a `mongosh` dependency; Node 24 (`node@24`) was re-linked as the default.

## Next task

PRs are open and linked: elinasarvari/benefit-be#1 and elinasarvari/benefit-fe#1. Merge them together after review. T150 (the full quickstart on a clean Mac account, timing section 1) is also still to do; sections 2 to 5 and 7 were exercised by hand and by tests.
