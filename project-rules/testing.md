# Testing conventions

Stack: backend is Python 3.11+ / FastAPI with `pytest`; frontend is React 19 + TypeScript (Vite) with Vitest + Testing Library. E2E and API tests use Playwright: see [quality-testing-playwright.md](quality-testing-playwright.md).

## General
- Follow red-green-refactor: write one failing test for a single behavior before writing implementation; never write multiple tests at once in the red phase.
- Name tests behavior-first: `test_<unit>_<scenario>_<expected>` in Python; `describe('<Unit>')` + `it('<expected> when <scenario>')` in Vitest.
- Structure every test with Arrange-Act-Assert; keep one logical outcome/assertion focus per test.
- Mock only collaborators across a boundary (DB, HTTP client, clock, LLM/model client, MCP tools); never mock value objects, Pydantic models or the unit under test. Prefer a hand-written fake for stateful interactions.
- Inject a fixed clock/seeded random for time- and randomness-dependent code; never call `datetime.now()`, `Date.now()` or an unseeded random generator directly in code under test.
- Refactor only with all tests green; rerun the full suite after every small refactor step, and address any surfaced security issue (parameterized queries, input validation, no hardcoded secrets) before merging.

## Backend (Python + FastAPI)
- `pytest` only (no `unittest.TestCase` classes); plain `assert` statements. Run with `pytest`; lint with `ruff check`.
- Tests live in `tests/`, mirroring the source folder structure; files are `test_<module>.py`.
- Shared setup goes in `conftest.py` fixtures; use `@pytest.mark.parametrize` for input variations instead of loops or copy-pasted tests.
- Endpoints: test through FastAPI's `TestClient` (or `httpx.AsyncClient` for async tests), and replace dependencies with `app.dependency_overrides`, not by patching module internals.
- Mock with `monkeypatch` or `unittest.mock` at the boundary; don't patch the function under test.
- Agents, workflows and rules follow the layer-specific testing rules in [backend-architecture.md](backend-architecture.md#testing) (no Temporal in agent tests, Temporal test environment for workflows, plain unit tests for rules).

## Frontend (React + TypeScript)
- Vitest + React Testing Library; co-locate tests as `Component.test.tsx` / `module.test.ts`.
- Query by role, label or text (`getByRole`, `getByLabelText`); `getByTestId` only as a last resort. Never assert on implementation details (component state, class names, hook internals).
- Simulate interactions with `@testing-library/user-event`, not `fireEvent`; use `findBy*`/`waitFor` for async UI instead of manual timers.
- Mock data access at the `src/api/` boundary (`vi.mock`), never `fetch` inside components; use `vi.useFakeTimers()`/`vi.setSystemTime()` for time-dependent code.
- Tests must type-check under strict mode; no `any` in tests without a comment.
