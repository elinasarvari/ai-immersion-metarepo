# Implementation Plan: Case Lifecycle

**Branch**: `feature/001-case-lifecycle` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-case-lifecycle/spec.md`

**Target repo**: `repos/benefit-be` only (no UI; screens are 006). No change in `repos/benefit-fe`.

## Summary

A durable `CaseWorkflow` (Temporal) drives each application from `submitted` to `decided`, calling stubbed verification (002) and determination (003) activities, opening a review task and waiting on a caseworker signal for every adverse or "cannot determine" result, and deciding with an outcome, reason code, coverage period and requested notice. The workflow is the only authority on transitions; one idempotent activity projects every change into MongoDB (`cases`, `case_events`, `review_tasks`, `caseworker_actions`, `coverage_periods`, `outbox`) in one transaction (ADR-001-01). The API opens the case in a guarded transaction and starts the workflow by a derived ID (ADR-001-02). Every date comes from a per-case clock (ADR-001-03).

## Technical Context

**Language/Version**: Python 3.12 (`repos/benefit-be/.python-version`; constitution requires 3.11+)

**Primary Dependencies**: temporalio 1.35.0, FastAPI 0.162.2, PyMongo 4.19.0 async, Pydantic v2 (pinned in `repos/benefit-be/pyproject.toml`). No new dependency (constitution X, PR-4).

**Storage**: MongoDB 8.0 single-node replica set, database `benefit` (+ `benefit_audit` for audit entries); new migration `0002_case_lifecycle` (KD-11).

**Testing**: pytest; Temporal time-skipping environment, replay and restart tests (TW-13–TW-16); integration against local MongoDB and Temporal (BA-9); contract tests on OpenAPI (`tests/contract/test_openapi.py`).

**Target Platform**: macOS native, `make dev` / `make prod` (PR-5, IX).

**Project Type**: web service (API + Temporal worker).

**Performance Goals**: none beyond the demo; no load testing (specs/README.md).

**Constraints**: workflow determinism (TW-1); no duplicate effects on retry (FR-001-04); calendar days in America/Chicago (FR-001-18, FR-000-27); synthetic data (PR-3).

**Scale/Scope**: demo seed of a few households; one open case per household.

## Constitution Check

| Principle | Status |
|---|---|
| I. AI assists, rules decide | Pass: outcome comes only from the `determine_eligibility` result (003 rules); no AI in 001. |
| II. Durable, deterministic orchestration | Pass: `CaseWorkflow` with `workflow.now()` only; side effects in activities; review waits are signal + `wait_condition` (ADR-001-01, TW-4). |
| III. Evidence for AI output | N/A in 001 (no AI output). |
| IV. Human control | Pass: every `ineligible` and `cannot_determine` result goes to a review task; override recorded with reviewer and reason (FR-001-09, FR-001-20). |
| V. Test-first | Pass: test levels in research R8; test names `test_FR_001_xx_…`; test plan by the quality engineer. |
| VI. Contracts first | Pass: `packages/domain/case.py`, `contracts/case-workflow.md`, `contracts/rest-api.openapi.yaml` merged in the contracts step. |
| VII. Clear boundaries | Pass: workflow imports no DB code (TW-2); API and worker talk through Temporal (BA-5). |
| VIII. Security, synthetic data | Pass: worker scope bound to case and household (ADR-001-06); applicants see only their household; reason text never logged. |
| IX. Local infrastructure | Pass: stubs behind activity names; settings from env (`DEMO_PROFILE`). |
| X. Simplicity | Pass: one workflow, one projection activity, no new services or dependencies. |

Re-checked after Phase 1 design: no violations. ADR-001-04 proposes a TW-5 amendment; the plan uses the compliant fallback.

## Project Structure

### Documentation (this feature)

```text
specs/001-case-lifecycle/
├── plan.md  research.md  data-model.md  quickstart.md  scope.json
├── contracts/case-workflow.md  contracts/rest-api.openapi.yaml
└── decisions/ADR-001-01 … ADR-001-06, README.md
```

### Source Code (`repos/benefit-be`, layout per `project-rules/backend-architecture.md`)

```text
packages/domain/
  case.py                 # [contracts] enums and models in data-model.md (BA-6, BA-8)
packages/platform/
  clock.py                # [platform-ui] + case_now, case_today (ADR-001-03)
  scope.py                # [platform-ui] + ScopeKind.worker, Scope.for_worker (ADR-001-06)
apps/worker/
  workflows/case.py       # [workflows] CaseWorkflow: run, caseworker_action signal, status + allowed_actions queries
  workflows/case_states.py# [workflows] transition table, coverage_for, deadline helpers (pure)
  workflows/calendar.py   # [workflows] + case-clock wrapper for workflow code
  activities/case_record.py   # [workflows] record_case_change (thin, TW-9)
  activities/verification.py  # [workflows] verify_documents stub (002 replaces body)
  activities/determination.py # [workflows] determine_eligibility stub (003 replaces body)
  repositories/cases.py   # [workflows] scoped queries and the transaction (database.md, KD-10)
  main.py                 # [workflows] register CaseWorkflow and activities
db/migrations/versions/
  0002_case_lifecycle.py  # [data] validators, unique/partial indexes, downgrade (KD-11)
apps/api/                 # [platform-ui] only if ADR-001-05 = Option A
  routers/applications.py  routers/cases.py
  services/cases.py        repositories/cases.py   schemas/cases.py
openapi/openapi.json      # [platform-ui] regenerated (FR-000-26)
tests/                    # mirrors the above (BA-9): apps/worker/workflows/test_case*.py,
                          # histories/case_*.json, integration/test_case_*.py, apps/api/routers/test_cases.py
```

**Structure Decision**: existing `benefit-be` layout; no new top-level folder (BA-1). Workflow imports only `packages/domain` and `packages/platform/clock` through `imports_passed_through` (as `calendar.py` does).

## Architecture decisions

| ADR | Decision | Status |
|---|---|---|
| ADR-001-01 | Workflow owns state; MongoDB projection by idempotent `record_case_change` | Accepted |
| ADR-001-02 | Case opened in a guarded API transaction; workflow ID `case-{uuid5(submission_reference)}` | Accepted |
| ADR-001-03 | Case clock parameters on the case; `case_now` pure function | Accepted |
| ADR-001-04 | Caseworker actions as updates (TW-5 amendment) | Proposed – needs amendment; plan uses fallback: signal + `allowed_actions` query |
| ADR-001-05 | 001 ships the three case endpoints (no UI) | Needs decision; plan assumes the recommendation, Option A |
| ADR-001-06 | `Scope.for_worker` for activity DB access | Accepted |

**Open questions**: ADR-001-05 (scope between 001 and 006; recommendation A). ADR-001-04 amendment (team, Governance); fallback B in use.

## Contracts between lanes

| Contract | Provider → consumers | Where |
|---|---|---|
| `packages/domain/case.py` models and enums | contracts step → all lanes, 006, 007, 008, 010, 011 | `data-model.md` |
| `CaseWorkflow` type, ID, `caseworker_action` signal, `status` / `allowed_actions` queries | Workflows → Platform & UI, 010, 011 | `contracts/case-workflow.md` |
| Activity names `verify_documents`, `determine_eligibility` and their I/O | Workflows ↔ Agents (002), Knowledge & data (003) | `contracts/case-workflow.md` |
| `cases`, `case_events`, `review_tasks`, `caseworker_actions`, `coverage_periods`, `outbox` schemas and indexes | Knowledge & data → Workflows, Platform & UI, 008 | `data-model.md`, migration `0002` |
| `case_now`, `Scope.for_worker` | Platform & UI → Workflows | ADR-001-03, ADR-001-06 |
| REST: `POST /applications`, `GET /cases/{id}`, `POST /cases/{id}/review-tasks/{task_id}/actions` | Platform & UI → benefit-fe (006) | `contracts/rest-api.openapi.yaml` (ADR-001-05) |

Order: contracts step (domain models, migration, OpenAPI) → lanes in parallel (workflows, platform-ui, data) → QA integration tests.

## Complexity Tracking

No constitution violations to justify.
