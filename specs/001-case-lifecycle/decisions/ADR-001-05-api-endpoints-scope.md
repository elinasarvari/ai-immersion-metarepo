# ADR-001-05: Does 001 ship the three case endpoints, or does 006?

- **Status:** Accepted – auto-decided
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-01, FR-001-07, FR-001-11, FR-001-23, US1-6, US3-1
- **Lanes affected:** Platform & UI | Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

This is a scope call between features. The spec map lists 001 as Workflows lane, target `benefit-be` only (specs/README.md "Feature map"), and 006 owns the REST API and screens (FR-006-07 submit, FR-006-09 history). But 001's acceptance scenarios need an entry point: refusal "with the reason" at submit (US1-6), "when its status is viewed" (US3-1), and a way for a caseworker to approve a denial (US1-3). Today the API has only auth and health routes (`repos/benefit-be/openapi/openapi.json`). The OpenAPI file is the contract with `benefit-fe` (PL-3) and goes in the Day 1 contracts PR (specs/000 research R23).

## Options

### Option A: 001 ships three thin endpoints in benefit-be, no UI
`POST /api/v1/applications` (submit, ADR-001-02), `GET /api/v1/cases/{case_id}` (state, deadline, days remaining, at-risk, history page), `POST /api/v1/cases/{case_id}/review-tasks/{task_id}/actions` (ADR-001-04). Routers → services → repositories (BA-2), role tests (PL-7). 006 builds screens on them and adds list endpoints.
- **Pros:** 001's acceptance scenarios are testable end to end through the API; the duplicate guard (US1-6) sits with the feature that defines it; 006 consumes a merged contract (VI).
- **Cons:** adds the Platform & UI lane to 001; 006's API surface is split across two features.

### Option B: 001 is worker-only; 006 adds every endpoint
001 tests through Temporal clients in workflow and integration tests; the `cases.py` service from ADR-001-02 is written by 006.
- **Pros:** lanes stay as in the feature map.
- **Cons:** US1-6 and US3-1 can't be demonstrated until 006; the guard logic is split from its requirement; 006 grows.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (US1-6, US3-1) within 001 | Yes | Only at workflow level |
| Constitution and rules (VI, PL-1/2/7, BA-2) | Yes | Yes |
| Simplicity (X) | Three endpoints | Fewer lanes in 001 |
| Testability | API integration tests | Workflow tests only |
| Fits feature map | Changes it | Matches |
| Effort | ~1 Platform & UI session | Moves to 006 |

## Decision

We choose **Option A: 001 ships three thin endpoints in benefit-be, no UI**.

- **Scope (least scope that meets every cited FR):** B does not meet FR-001-23 / US1-6 within 001. Accepted ADR-001-02 puts the duplicate guard and the synchronous "refused with the reason" in the API service `apps/api/services/cases.py`; under B that service moves to 006, so 001's own requirement would be unproven until 006. Likewise the 409 pre-check that Accepted-auto ADR-001-04 (Option B) relies on for US1-5 lives in the action endpoint. A is therefore the smallest option that meets FR-001-01, FR-001-05, FR-001-11, FR-001-23, US1-3, US1-5, US1-6 and US3-1 in this feature.
- **Least scope within A:** only the three endpoints, no UI and no list endpoints (those stay in 006); `benefit-fe` client regeneration is deferred to 006's PR (PL-3), since 001 has no UI.
- **Rules and constitution:** A is compliant with VI (006 consumes a merged contract), PL-1/2/7 and BA-2; the only cost is a feature-map lane change for 001 (Platform & UI added), which is planning, not a rule.
- Matches the architect's recommendation.

**Decided by:** decision-maker (automated), 2026-11-10; architect recommended Option A
**Revisit if:** 006 is scheduled to merge before or together with 001 (the endpoints would then fit 006's API surface without leaving 001 unproven), or the team rules that features must keep the lanes in the feature map.

Architect's rationale: It keeps the refusal reasons and the deadline view next to the requirements that define them, and gives 006 a merged contract. The plan, `scope.json` (adds `platform-ui-lane`) and `contracts/rest-api.openapi.yaml` assume A. If B is chosen, drop the Platform & UI lane from `scope.json` and move `contracts/rest-api.openapi.yaml` to 006; the workflow contracts are unchanged.

## Consequences

- **Good (A):** independent tests of US1 and US3 run against the API.
- **Bad / accepted trade-offs (A):** OpenAPI change in 001 must be paired with a `benefit-fe` client regeneration (PL-3); recommendation: regenerate in 006's PR, since 001 has no UI.
- **Work this creates (A):** Platform & UI: `routers/cases.py`, `routers/applications.py`, `services/cases.py`, `repositories/cases.py`, `schemas/cases.py`, OpenAPI export.

## How we verify it

Contract test `tests/contract/test_openapi.py` (drift, existing); role-rejection tests per route (PL-7); `tests/contract/test_every_route_protected.py` (existing) covers the new routes.

## References

PL-1, PL-2, PL-3, PL-7; BA-2; constitution VI; specs/README.md feature map; FR-006-07, FR-006-09.
