# platform-ui-lane: blocked

## benefit-be tasks T025, T026, T027, T028, T043, T044 (not started)

`repos/benefit-be` on `feature/003-eligibility-rules` is 9 commits behind `origin/main` (the integrator has not merged it yet, ADR-003-04). These tasks edit files that exist only on main, so writing them now would create files that clash with main's:

- `apps/api/routers/cases.py`, `services/cases.py`, `repositories/cases.py`, `schemas/cases.py` (the route, role guard and `CaseDetail` pattern T026 copies from)
- `packages/platform/scope.py` on main has `Scope.for_worker`, `ScopeKind.worker` and `household_stub_results`, which T025 changes and TC-102 uses
- `tests/db/test_scope.py`, `tests/apps/api/routers/test_cases.py`, `tests/contract/test_every_route_protected.py`

Do after the integrator merges `origin/main`: T043 and T044 (tests first, TC-102 to TC-115), then T025, T026, T027, then T028 (regenerate `openapi/openapi.json`).

The OpenAPI shape to produce is `specs/003-eligibility-rules/contracts/rest-api.openapi.yaml` (`listCaseDeterminations`, `DeterminationList`, `DeterminationView`, `RuleResult`, `MissingItem`).

## benefit-fe T029: vendored OpenAPI is ahead of benefit-be

`openapi/openapi.json` and `src/api/generated/schema.d.ts` were regenerated from a copy of the contract added to the vendored spec, because benefit-be's `openapi/openapi.json` does not have the path yet. Until T028 lands, `src/api/generated.test.ts` "the vendored openapi file matches the sibling benefit-be checkout" fails (the only failing FE unit test). After T028, run `BE_LOCAL=1 pnpm api:gen` in benefit-fe; if FastAPI's output differs from the hand-built entries, the regenerated file wins and `DeterminationSection` / `determinations.ts` need only type fixes.

## Not run

`e2e/caseworker-sees-determination.spec.ts` (T031, TC-124 to TC-128) needs the API route, the seeded demo households and the stack; it type-checks, lints and is listed by Playwright, but has not been run. The spec shares households with the other journeys in the `-journeys` phase, so run it after `make seed-reset`, and move it into a serial phase if it races.
