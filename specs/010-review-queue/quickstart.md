# Quickstart: 010 Review queue and caseworker actions

Run from `repos/benefit-be` (targets from its `Makefile`).

1. `make dev` (MongoDB replica set, Temporal dev server, worker, API). `make reset` rebuilds the data; confirm it applies migration `0002_review_queue` (unverified: the migration runner entry point is `db/migrate.py`).
2. Workflow tests (time-skipping, stubbed activities, TW-13/TW-15): `make test-workflow PYTEST_ARGS="-k FR_010"`
3. Integration tests (local MongoDB + Temporal, BA-9): `make test-integration PYTEST_ARGS="-k FR_010"`
4. Manual check in the demo profile (`DEMO_PROFILE=true`, one day per minute, FR-011-04):
   - A case whose stubbed determination is Ineligible → an `adverse_determination` task in `review_tasks`.
   - After 2 minutes `flags` contains `reminder`; after 4 minutes `escalated`.
   - The same `caseworker_action` sent twice with one `action_id` → one `applied` record in `caseworker_actions`.
5. `make check` before any PR (PR-6).
