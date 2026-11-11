# workflows-lane: blocked and cross-lane items (010-review-queue)

## Not done

- **T018** (compose `review.py` into `CaseWorkflow`): blocked by 001, because `apps/worker/workflows/case.py` doesn't exist yet. `ReviewHarnessWorkflow` stands in for it and is registered in `apps/worker/main.py`. When 001 lands: mix in `ReviewHandlers`, build `ReviewLoop` in `run`, start `loop.run()` as a task, call `open_review` / `verify_documents` / `evaluate` / `request_information_automatically` at the raising points (see `review_harness.py::_raise`), and pass real `CaseTransitions` and `CaseClock` implementations instead of the stubs in `review_ports.py`.
- **T019**: partly done. The PL-11 log check passed: no free-text `reason`, corrected value or applicant data is logged in `review.py`, the activities or the repositories, and TC-40 covers it. What's still open:
  - `make check` fails on `tests/packages/platform/test_settings.py::test_FR_000_03_env_example_lists_every_setting`, because `.env.example` doesn't list `REVIEW_REMINDER_DAYS` or `REVIEW_ESCALATION_DAYS`. This is **[contracts] T002**, which is still open. Every other unit, workflow and contract test passes (330), and so do ruff and mypy.
  - The integration tests TC-10, TC-17, TC-18, TC-19 and TC-20 (`tests/apps/worker/repositories/`) are written but haven't been run. This machine has no `.env` or MongoDB settings (`MONGO_URL_APP` etc. are missing; the existing `tests/db` suite fails the same way). So T005 and T006 are only verified for type and lint, not against MongoDB.
  - Quickstart steps 1, 3 and 4 need `make dev` and migration 0002 (data-lane).

## Changes needed in other lanes

- **[data] T003 / migration 0002:** the validators must accept what the worker writes:
  - `review_tasks`: `_id` is the task ID, and there is **no** `task_id` field. The other fields come from `ReviewTask`, with `decision_deadline` and `coverage_end` stored as UTC-midnight dates.
  - `caseworker_actions`: `_id` = `action_id`, plus an `action_id` field and every `CaseworkerAction` field.
  - `eval_overrides`: `_id`, `action_id`, `household_id`, `case_id`, `task_id`, `action`, `finding_id`, `field_ref`, `corrected_value`, `reviewer_id`, `recorded_at`.
- **[data] `eval_overrides.finding_unique`** (0001) is a plain unique index on `finding_id`. A `correct_value` on a Cannot-determine task has no `finding_id`, so the second such override collides on `null`. Make it a partial index (`finding_id` of type binData) in 0002.
- **[contracts] (BA-8):** the 001/002/003 stub payloads in `apps/worker/workflows/review_ports.py` should move to `packages/domain` with those features' contracts: `CaseStep`, `ReviewResult`, `CaseRef`, `VerificationFinding`/`VerificationResult`, `EvaluationResult`, `DraftRequestInput`/`DraftRequestResult` and `AdvanceClock`.
- **[contracts], optional:** `packages/domain/audit.py::ReasonCode` has no value for the review rejection codes. Refusal audit entries (R8) therefore carry no `reason_code`; the code is in `caseworker_actions.rejection_code`.
- **Starters (001/011/API):** whoever starts a case workflow must pass `ReviewWindowSettings.from_settings(settings)` and the case-clock scale in the workflow input. Workflows never read settings (TW-1).
