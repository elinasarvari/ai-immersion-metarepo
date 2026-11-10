# data-lane: blocked / handoffs (010-review-queue)

Nothing outside `db/` and `tests/db/` was edited. Notes for other lanes:

1. **Not run here (environment)**: TC-35–TC-38 and `tests/db/test_migrations.py` need `.env` (MONGO_URL_*, secrets) and a running `make mongo-up`; neither was available to this lane's session. Run `uv run pytest tests/db -q` before merging. Lint, format and mypy on the lane's files pass.
2. **workflows-lane (T005/T006 repositories)**: the `0002_review_queue` validators store `decision_deadline` and `coverage_end` as BSON dates (midnight UTC), so convert `datetime.date` to `datetime` before writing. `review_tasks` requires `_id` (UUID = `task_id`); `task_id` is also allowed. `caseworker_actions` requires `_id` (UUID or ObjectId) and enforces unique `action_id` (`action_id_unique`); `reason` must be 1–500 characters or null. `additionalProperties: false` on both, so only the fields in data-model.md are accepted.
3. **Shared**: `tests/db/test_migrations.py::test_migration_runner_records_and_skips_applied_versions` was updated (data-lane test) to expect `0001_baseline` and `0002_review_queue`.
