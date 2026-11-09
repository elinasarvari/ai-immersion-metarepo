# Quality testing: E2E and API tests (Playwright)

Playwright covers the layers above unit tests: full user journeys through the UI (E2E) and HTTP contract checks against the running API. Unit/component tests stay as defined in [testing.md](testing.md), [frontend-react.md](frontend-react.md) and [backend-python.md](backend-python.md).

## Where tests live

| Suite | Repo / folder | Tooling | Run |
|---|---|---|---|
| E2E (UI) | `benefit-fe/e2e/` | `@playwright/test` (TypeScript) | `npx playwright test` |
| API | `benefit-be/tests/api/` | `pytest` + `pytest-playwright` (`APIRequestContext`) | `pytest tests/api` |

- One spec file per user journey (`e2e/<journey>.spec.ts`) or API resource (`tests/api/test_<resource>.py`); shared setup goes in fixtures, not copy-pasted `beforeEach` blocks.
- E2E uses the Page Object Model in `e2e/pages/`; specs never contain raw selectors.
- Base URLs, credentials and tokens come from env vars (`E2E_BASE_URL`, `API_BASE_URL`, ...) with defaults in a committed `.env.example`; never hardcode them.

## What to cover
- Every user story's acceptance scenarios from `specs/<NNN-feature>/spec.md` get at least one E2E test for the happy path; name the test after the scenario, starting with the requirement ID it proves (`test('FR-000-19: applicant blocked from another household', ...)`). API tests follow the Python form in [testing.md](testing.md) (`test_FR_006_05_...`).
- Every API endpoint gets API tests for: success response and schema, validation errors (`422`), auth (`401`/`403`), not found (`404`), and any documented business-rule error.
- Validate API response bodies against the OpenAPI schema / `packages/domain` Pydantic models, not just status codes.
- Don't re-test business logic exhaustively in E2E; push edge cases down to unit or API tests (test pyramid).

## E2E rules
- Locate elements by user-facing role, label or text (`getByRole`, `getByLabel`, `getByText`); fall back to `data-testid` only when no accessible locator exists. No CSS/XPath tied to layout.
- Use web-first assertions (`await expect(locator).toBeVisible()`); never use `waitForTimeout` or fixed sleeps.
- Each test is independent: create its own data (via API calls or fixtures) and doesn't depend on test order or leftovers from other tests.
- Log in once with a setup project and reuse `storageState`; don't drive the login UI in every test.
- Mock third-party services with `page.route()`; hit our own API for real.
- Run Chromium on every PR; Firefox and WebKit on `main`/nightly.
- Include an accessibility check (`@axe-core/playwright`) on each key page; fail on serious/critical WCAG 2.1 AA violations.

## API test rules
- Use `APIRequestContext` against the running FastAPI server; don't import app internals or call services directly (that's what unit tests are for).
- Seed and clean up data through the API or dedicated fixtures; never rely on a shared, hand-maintained database state.
- Assert on error response shape too, and check that no stack traces or internal details leak (see [security.md](security.md)).
- Workflow-triggering endpoints: assert the API response and the signal/start contract; long-running Temporal behavior is tested in the worker's own tests ([backend-architecture.md](backend-architecture.md)).

## CI and reliability
- E2E and API suites run in CI on every PR against an ephemeral environment (`make dev` stack or containers), and must pass before merge.
- Config: `retries: 2` in CI only (0 locally), `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`; upload the HTML report and traces as CI artifacts.
- A test that passes only on retry is flaky: fix it or quarantine it with `test.fixme` plus a linked issue. Don't raise timeouts or retries to hide it.
- Keep the suites fast: run in parallel (`fullyParallel: true`), tag slow or broad suites (`@slow`, `@smoke`), and run `@smoke` on every PR when the full suite is too slow.
