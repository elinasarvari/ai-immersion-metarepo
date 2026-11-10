# ADR-001-06: A case-bound worker scope for activity database access

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-10, FR-001-22, FR-001-23
- **Lanes affected:** Platform & UI | Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

Every repository query takes a `Scope` (specs/000 research R16; `repos/benefit-be/packages/platform/scope.py:60`). Only two kinds exist: `user` (from a `Principal`) and `system` (from a verified agent-tool credential, `Scope.for_system`, line 70). A `system` scope is limited to `case_id` and is refused on household-only collections such as `coverage_periods` (lines 92–94). 001's activities must write `cases`, `case_events`, `review_tasks`, `outbox` and create a `coverage_periods` record (FR-001-22). The worker has no user, and the agent credential is meant only for MCP tools (FR-000-22, PL-6).

## Options

### Option A: New `ScopeKind.worker`, bound to the case and household from the workflow input
`Scope.for_worker(case_id, household_id)`, built only in `apps/worker/activities/`. Case-scoped collections filter on `case_id`; household-only collections (`coverage_periods`) filter on `household_id`; `households`/`users` stay refused.
- **Pros:** least privilege per case; one helper; the registry keeps refusing unknown collections.
- **Cons:** a change to `packages/platform/scope.py` (Platform & UI lane) and its tests.

### Option B: Mint a system credential in every DB activity
Reuse `issue_system_credential` and `Scope.for_system`.
- **Pros:** no new scope kind.
- **Cons:** misuses the agent-tool credential; still refuses `coverage_periods`; adds signing to every write.

### Option C: Caseworker-like unscoped access for the worker
- **Pros:** simplest.
- **Cons:** no household limit at all for system code; weakens constitution VIII.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-001-22) | Yes | No | Yes |
| Constitution and rules (VIII, PL-6, R16) | Yes | Strains PL-6 | Weakens VIII |
| Simplicity (X) | Medium | Low | High |
| Security and privacy | Case + household bound | Case bound | None |
| Testability | Extends `tests/packages/platform/test_scope_filter.py` | Same | – |
| Fits existing code | Same pattern as `for_system` | Yes | No |
| Reversibility | High | High | Low |

## Decision

We choose **Option A**: it gives activities exactly the case and household they work on, keeps the agent credential for tools only, and follows the existing `Scope` pattern.

## Consequences

- **Good:** coverage creation and the duplicate-application read (household) are covered by the same isolation checks as the API.
- **Bad / accepted trade-offs:** the worker trusts the IDs in its own workflow input (accepted: only the API starts workflows, after authorization).
- **Work this creates:** Platform & UI: `ScopeKind.worker`, `Scope.for_worker`, filter branch and tests in `packages/platform/scope.py`. Workflows: activities build the scope from `CaseStart`.

## How we verify it

Unit tests: worker scope adds `case_id` on case collections, `household_id` on `coverage_periods`, and refuses `households` and `users` (CI). Existing scan test for unscoped `find` calls keeps covering activities (R16).

## References

Constitution VIII; PL-6; FR-000-22; specs/000 research R6, R16; `database.md`.
