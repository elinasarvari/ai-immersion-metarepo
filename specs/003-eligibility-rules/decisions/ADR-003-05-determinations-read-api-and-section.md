# ADR-003-05: A determinations sub-resource and its own case page section

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-23, FR-003-05, US5
- **Lanes affected:** Platform & UI
- **Repos affected:** benefit-be, benefit-fe
- **Supersedes:** –

## Context

The caseworker case page must show each determination with its per-rule trace (FR-003-23). On main, `GET /api/v1/cases/{case_id}` returns `CaseDetail` (`benefit-be@main:apps/api/routers/cases.py`, `get_case`) and the page renders sections from a registry that "a later feature adds its section here and nowhere else" (`benefit-fe@main:src/features/caseworker/case-page/sections.tsx`). History is already a sub-resource (`/cases/{case_id}/history`, caseworker only). The API must not call `packages/rules` (BA-4, PL-2); it reads stored records.

## Options

### Option A: `GET /api/v1/cases/{case_id}/determinations` + `DeterminationSection`
Caseworker and supervisor roles; returns `{items: DeterminationView[]}` newest first (a case has at most a few). Service reads `determinations` through a scoped repository; read is audited (research R11). In benefit-fe, a `useCaseDeterminations` query and a `DeterminationSection` registered in `caseSections`, visible when the case has reached `determining` or later.
- **Pros:** additive OpenAPI change; follows the history pattern; `CaseDetail` (shared with applicants) is untouched.
- **Cons:** one more request per page.

### Option B: Embed determinations in `CaseDetail`
- **Cons:** changes 001's response used by applicants (would need per-role field hiding); larger payload on every poll.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (FR-003-23) | yes | yes |
| Constitution and rules (PL-2, PL-3, FE-3, FE-6) | yes | contract change to 001 |
| Simplicity (X) | high | medium |
| Security and privacy | role-guarded endpoint | per-role filtering risk |
| Testability | route + role rejection tests | more cases |
| Fits existing code and ADRs | matches `/history` and R15 | no |
| Reversibility | high | low |
| Effort | low | medium |

## Decision

We choose **Option A**: additive, role-guarded, and the pattern 001 established for history and sections.

## Consequences

- **Good:** applicants never receive per-rule inputs; benefit-fe change is one section.
- **Bad / accepted trade-offs:** a second fetch on the case page.
- **Work this creates:** [contracts] `contracts/rest-api.openapi.yaml` path, `DeterminationView` schema; [platform-ui, be] `apps/api/routers/cases.py` route, `services/determinations.py`, `repositories/determinations.py`, `schemas/determinations.py`, export `openapi/openapi.json`; [platform-ui, fe] regenerate client, `src/api/determinations.ts`, `DeterminationSection.tsx` + tests, register in `sections.tsx`, an e2e journey for US5.

## How we verify it

`tests/contract/test_every_route_protected.py` and role rejection tests (applicant → 403) (PL-7); OpenAPI drift check (`tests/contract/test_openapi.py`, FE `scripts/check-api.mjs`); FE component tests for the three results; Playwright US5 journey with axe check.

## References

PL-2, PL-3, PL-5, PL-7, FE-3, FE-4, FE-6, FE-10, BA-4, constitution IV, VIII.
