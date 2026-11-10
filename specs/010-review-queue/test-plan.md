# Test plan: 010-review-queue

Quality engineer: test-strategy skill, 2026-11-10. Inputs: spec.md, plan.md, data-model.md, contracts/workflow-review.md, research.md, ADR-010-01 … 06, tasks.md. Existing tests read: `tests/apps/worker/{test_policies.py, workflows/test_smoke*.py, histories/}`, `tests/db/test_migrations.py`, `tests/integration/`, `tests/contract/`.

Files (all in `repos/benefit-be`):
- `tests/packages/domain/test_review.py` (contracts)
- `tests/packages/platform/test_settings.py` (contracts, settings item)
- `tests/apps/worker/test_policies.py`, `tests/apps/worker/workflows/test_review_validate.py`, `test_review_timers.py`, `test_review.py`, `test_review_failures.py`, `test_review_flags.py`, `test_review_replay.py`, `test_review_restart.py`, `histories/review_v1.json`, `tests/apps/worker/activities/test_review_tasks.py`, `tests/apps/worker/repositories/test_review_tasks.py`, `test_caseworker_actions.py` (workflows)
- `tests/db/migrations/test_0002_review_queue.py` (data)
- `tests/integration/test_review_queue.py`, `tests/contract/test_review_contract.py` (qa)

## Cases

| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-010-01, SC-010-01, FR-001-19 (old ID) | unit | contracts / benefit-be | `test_FR_010_01_allowed_actions_table_matches_spec` | parametrize 6 reasons → exact `frozenset` from FR-010-01 table |
| TC-02 | FR-010-01, FR-010-05 | unit | contracts / benefit-be | `test_FR_010_01_reason_required_ai_overrides_and_blocking_sets_match_spec` | constants only; `explanation_review` not blocking |
| TC-03 | FR-010-05 | unit | contracts / benefit-be | `test_FR_010_05_signal_reason_length_bounds_and_extra_fields_rejected` | reason `""`, 1, 500, 501 chars; unknown field → `ValidationError` |
| TC-04 | FR-010-01, US1-AS1, FR-011-02 (missed window raises review, stubbed) | workflow | workflows-lane / benefit-be | `test_FR_010_01_report_opens_task_with_reason_evidence_and_case_waits` | parametrize 6 reasons with causes; synthetic UUIDs; stub activities (TW-15) |
| TC-05 | FR-010-01, US1-AS2, SC-010-01, FR-001-10 (action recorded) | workflow | workflows-lane / benefit-be | `test_FR_010_01_allowed_action_resumes_with_listed_result_and_records_reviewer` | parametrize all 16 allowed (reason, action) pairs; reviewer, `applied_at_case`, reason recorded |
| TC-06 | FR-010-05, US1-AS3 | unit | workflows-lane / benefit-be | `test_FR_010_05_action_not_allowed_for_reason_refused` | parametrize every disallowed pair (6 × 11 − 16) → `not_allowed_for_reason` |
| TC-07 | FR-010-05, US1-AS3 | workflow | workflows-lane / benefit-be | `test_FR_010_05_disallowed_action_recorded_rejected_and_task_stays_open` | `approve` on `adverse_determination` |
| TC-08 | FR-010-05, US1-AS4 | unit | workflows-lane / benefit-be | `test_FR_010_05_star_action_without_reason_refused` | parametrize 5 * actions × reason `None` → `reason_required` |
| TC-09 | FR-010-06, US1-AS5, SC-010-04 | workflow | workflows-lane / benefit-be | `test_FR_010_06_same_action_id_signalled_twice_applied_once` | two signals, one `action_id`; one transition, one record call |
| TC-10 | FR-010-06, SC-010-04 | integration | workflows-lane / benefit-be | `test_FR_010_06_record_duplicate_action_id_keeps_one_document` | local MongoDB; same `CaseworkerAction` twice |
| TC-11 | FR-010-01, FR-001-20 | workflow | workflows-lane / benefit-be | `test_FR_010_01_override_to_approve_decides_approved_and_keeps_determination` | stub determination Ineligible; `override_action_id` set, determination unchanged (PR-1, R7) |
| TC-12 | FR-010-04, FR-001-21 (old ID) | workflow | workflows-lane / benefit-be | `test_FR_010_04_caseworker_request_information_drafted_after_auto_request_used` | `auto_rfi_used=True`; `draft_request` stub called once |
| TC-13 | FR-010-01 | unit | workflows-lane / benefit-be | `test_FR_010_01_second_extension_for_same_request_refused` | same `request_id` twice → `extension_already_used`; other `request_id` allowed |
| TC-14 | FR-010-01 | workflow | workflows-lane / benefit-be | `test_FR_010_01_edit_and_approve_keeps_draft_and_revision` | notice and explanation reasons; `revision_id` recorded (R5) |
| TC-15 | FR-010-01, FR-004-11 (failed explanation check, stubbed) | workflow | workflows-lane / benefit-be | `test_FR_010_01_explanation_review_does_not_block_decision` | `open_review` returns immediately; decision proceeds |
| TC-16 | FR-010-05 | unit | workflows-lane / benefit-be | `test_FR_010_05_action_on_closed_task_refused_task_closed` | closed task → `task_closed` |
| TC-17 | FR-010-01, FR-002-11, FR-006-02 | integration | workflows-lane / benefit-be | `test_FR_010_01_ai_override_writes_eval_override_in_same_transaction` | `correct_value`, `dismiss_finding`; forced failure on 2nd insert rolls back both (R6) |
| TC-18 | FR-010-05 | integration | workflows-lane / benefit-be | `test_FR_010_05_rejected_action_writes_audit_refused` | `audit_log` `caseworker_action` / `refused` (R8) |
| TC-19 | FR-010-01 | integration | workflows-lane / benefit-be | `test_FR_010_01_repository_writes_scoped_to_household_and_case` | two synthetic households; other household's task untouched (constitution VIII) |
| TC-20 | FR-010-02 | integration | workflows-lane / benefit-be | `test_FR_010_02_set_flag_and_close_ignored_on_closed_task` | closed task; no update |
| TC-21 | FR-010-03, US2-AS1, SC-010-02, FR-001-12 (old ID) | workflow | workflows-lane / benefit-be | `test_FR_010_03_verification_fails_3_times_opens_verification_review` | `verify_documents` stub always raises retryable; 3 attempts; cause `retry_limit_reached`; workflow running |
| TC-22 | FR-010-03, US2-AS2, SC-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_03_determination_fails_3_times_opens_review_and_does_not_stall` | `evaluate` stub raises; `cannot_determine` / `determination_failed` (ADR-010-05 A) |
| TC-23 | FR-010-03, SC-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_03_non_retryable_error_opens_review_after_1_attempt` | `ValidationError`; cause `non_retryable_error` |
| TC-24 | FR-010-03 | unit | workflows-lane / benefit-be | `test_FR_010_03_rules_step_allows_3_attempts` | `RULES_STEP.retry_policy.maximum_attempts == 3` |
| TC-25 | FR-010-04 | workflow | workflows-lane / benefit-be | `test_FR_010_04_second_automatic_request_opens_verification_review` | two findings; `draft_request` once, then `verification_review` |
| TC-26 | FR-010-02 | unit | workflows-lane / benefit-be | `test_FR_010_02_reminder_due_at_exactly_2_case_days` | 1d23h59m → not due, 2d → due; UTC (FR-000-27); ADR-010-06 A |
| TC-27 | FR-010-02 | unit | workflows-lane / benefit-be | `test_FR_010_02_escalation_due_is_earlier_of_4_days_and_coverage_end` | coverage end before, after, `None` |
| TC-28 | FR-010-02, US3-AS1, SC-010-03, FR-001-08 (old ID), FR-001-13 (case clock) | workflow | workflows-lane / benefit-be | `test_FR_010_02_task_open_2_days_marked_reminder` | time-skipping; `set_review_flag(reminder)` once (TW-13) |
| TC-29 | FR-010-02, US3-AS2, SC-010-03 | workflow | workflows-lane / benefit-be | `test_FR_010_02_task_open_4_days_flagged_escalated` | time-skipping |
| TC-30 | FR-010-02, US3-AS3, FR-007-04 (coverage end, stubbed) | workflow | workflows-lane / benefit-be | `test_FR_010_02_coverage_end_passes_redetermination_task_escalated` | coverage end at day 1 → escalated at day 1 |
| TC-31 | FR-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_02_action_at_reminder_time_wins_and_no_flag_set` | action signalled at the timer instant |
| TC-32 | FR-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_02_advance_clock_brings_reminder_forward` | case-clock stub advanced 2 days (011 advance-clock) |
| TC-33 | FR-010-01, FR-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_01_review_history_replays_without_nondeterminism` | `histories/review_v1.json`: open, reminder, action (TW-14) |
| TC-34 | FR-010-01, FR-010-02 | workflow | workflows-lane / benefit-be | `test_FR_010_01_open_task_and_timers_survive_worker_restart` | restart mid-wait; reminder still fires, action applies (TW-16) |
| TC-35 | FR-010-01 | integration | data-lane / benefit-be | `test_FR_010_01_review_tasks_validator_rejects_unknown_reason_and_extra_fields` | migration 0002 on test DB |
| TC-36 | FR-010-06 | integration | data-lane / benefit-be | `test_FR_010_06_caseworker_actions_unique_action_id_index` | duplicate insert → `DuplicateKeyError` |
| TC-37 | FR-010-01 | integration | data-lane / benefit-be | `test_FR_010_01_migration_0002_down_restores_baseline` | up, down, up |
| TC-38 | FR-010-02 | integration | data-lane / benefit-be | `test_FR_010_02_queue_and_escalated_queries_use_indexes` | `explain()` on `{status, decision_deadline}` and `{status, flags, decision_deadline}` |
| TC-39 | FR-010-02 | unit | contracts / benefit-be | `test_FR_010_02_review_settings_default_2_and_4_and_escalation_after_reminder` | settings; escalation ≤ reminder → error |
| TC-40 | FR-010-05 | unit | workflows-lane / benefit-be | `test_FR_010_05_free_text_reason_never_logged` | structlog capture during apply and reject (PL-11) |
| TC-41 | FR-010-01 | unit | workflows-lane / benefit-be | `test_FR_010_01_upsert_review_task_activity_is_idempotent` | fake repository; called twice → same document (TW-11) |
| TC-42 | FR-010-01, SC-010-01 | integration | qa / benefit-be | `test_FR_010_01_ineligible_case_opens_adverse_task_in_review_tasks` | Temporal dev server + MongoDB with 0002 applied; stub determination; seed household (BA-11) |
| TC-43 | FR-010-06, SC-010-04 | integration | qa / benefit-be | `test_FR_010_06_signal_sent_twice_one_applied_record` | quickstart step 4 |
| TC-44 | FR-010-02, SC-010-03, FR-011-04 (demo time scale) | integration | qa / benefit-be | `test_FR_010_02_demo_profile_reminder_and_escalation_flags_in_projection` | `DEMO_PROFILE=true`, one day per minute (FR-011-04) |
| TC-45 | FR-010-03, SC-010-02 | integration | qa / benefit-be | `test_FR_010_03_failing_verification_projects_review_task` | stub agent raises; task visible in `review_tasks` |
| TC-46 | FR-010-01 | contract | qa / benefit-be | `test_FR_010_01_signal_query_and_payloads_match_workflow_contract` | `caseworker_action`, `open_review_tasks`, payload models from `packages/domain/review.py` |

Level counts: unit 13, workflow 19, integration 13, contract 1, e2e 0, eval 0.

## Quality gates
- Coverage: every FR has ≥1 case (checked by `wf.py test-plan-check` and `wf.py trace`); every acceptance scenario US1-AS1…5, US2-AS1…2, US3-AS1…3 and every edge case has a case.
- Workflow rules: time-skipping for each signal and timer (TW-13), replay (TW-14), stubbed activities (TW-15), restart (TW-16).
- No live model, agent or Anthropic call in any test (FR-000-20); synthetic data only (PR-3).
- `make check` green (PR-6); `pytest -m "workflow or integration" -k FR_010` green.
- Evals: none — 010 produces no AI output; AI overrides only feed `eval_overrides` (TC-17).
- Not tested, and why: queue screens and the action REST endpoint (006, out of scope); e2e journey belongs to 006.

## Notes for the team
- TC-22 and TC-26–TC-30 assert the ADR-010-05 / ADR-010-06 recommendations; if the decision changes, update those expected values only.
