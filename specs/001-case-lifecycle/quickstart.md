# Quickstart: validate 001 Case lifecycle

Target: `repos/benefit-be`. Contracts in `contracts/`, models in `data-model.md`.

## Prerequisites
- `make doctor` passes; `make mongo-up`, then `make reset` (applies migrations including `0002_case_lifecycle`, then seeds; check the target in `Makefile`).
- `make dev` running (API, worker, Temporal dev server).

## Automated checks
```bash
cd repos/benefit-be
make test-workflow      # time-skipping, replay, restart (US1, US2)
make test-integration   # guards, idempotency (FR-001-04, FR-001-23)
make test-contract      # OpenAPI drift, route protection
make openapi-check
make check
```

## Manual journey (stubs on)
1. Sign in as the demo applicant; `POST /api/v1/applications` with a new `submission_reference` → 201, `state` moves to `verifying`, `decision_deadline` = receipt + 45 days.
2. Repeat the same request → 200 with the same `case_id`. A new reference for the same household → 409 `household_has_open_case`.
3. Stub determination `eligible` → `GET /api/v1/cases/{id}` shows `decided`, `approved`; a `coverage_periods` record starts the first of the receipt month; an `approval` outbox record exists.
4. Stub `ineligible` → `under_review` with an `adverse_determination` task; `POST .../actions` `approve_denial` as a caseworker → `decided`, `denied`, reason code from the determination, `denial` outbox record. `override_to_approve` without a reason → 422.
5. Stub `cannot_determine` → review task listing missing items; never decided automatically.
6. Stop the worker while the case is `verifying` or waiting on a task; restart → same step, no second task, event or notice.
7. With `DEMO_PROFILE=true`, `case_events` show both `case_time` and `real_time`.
