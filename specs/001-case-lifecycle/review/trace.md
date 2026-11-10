# Requirement traceability

Mode: strict. A test counts only where it is defined (a Python `def`, a `test(`/`it(` title, or an eval case id) and not skipped.

| Case | Proves | Level | Test | Defined in |
|---|---|---|---|---|
| TC-01 | FR-001-01, FR-001-23 | unit | `test_FR_001_01_case_id_for_same_reference_is_stable` | benefit-be:tests/packages/domain/test_case.py |
| TC-02 | FR-001-11 | unit | `test_FR_001_11_case_status_at_risk_at_ten_days_or_fewer` | benefit-be:tests/packages/domain/test_case.py |
| TC-03 | FR-001-20 | unit | `test_FR_001_20_override_request_requires_reason_up_to_500_chars` | benefit-be:tests/packages/domain/test_case.py |
| TC-04 | FR-001-13 | unit | `test_FR_001_13_case_now_follows_scale_and_offset` | benefit-be:tests/packages/platform/test_clock.py |
| TC-05 | FR-001-18, FR-000-27 | unit | `test_FR_001_18_case_today_is_chicago_date_across_dst_and_midnight_utc` | benefit-be:tests/packages/platform/test_clock.py |
| TC-06 | FR-001-23, FR-001-22 | unit | `test_FR_001_23_worker_scope_filters_coverage_by_household_and_refuses_households` | benefit-be:tests/packages/platform/test_scope_filter.py |
| TC-07 | FR-001-10 | unit | `test_FR_001_10_worker_scope_filters_case_collections_by_case_id` | benefit-be:tests/packages/platform/test_scope_filter.py |
| TC-08 | FR-001-01 | unit | `test_FR_001_01_decision_deadline_is_45_calendar_days_after_receipt` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-09 | FR-001-02 | unit | `test_FR_001_02_only_table_transitions_are_allowed` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-10 | FR-001-02 | unit | `test_FR_001_02_transitions_reserved_for_010_and_011_are_refused` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-11 | FR-001-22 | unit | `test_FR_001_22_coverage_starts_first_of_receipt_month_ends_last_day_of_12th_month` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-12 | FR-001-22 | unit | `test_FR_001_22_coverage_is_always_twelve_whole_months_property` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-13 | FR-001-18 | unit | `test_FR_001_18_deadline_minus_receipt_is_always_45_days_property` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-14 | FR-001-07 | unit | `test_FR_001_07_allowed_actions_for_001_review_reasons` | benefit-be:tests/apps/worker/workflows/test_case_states.py |
| TC-15 | FR-001-16 | unit | `test_FR_001_16_stub_determination_follows_household_stub_field` | benefit-be:tests/apps/worker/activities/test_stubs.py |
| TC-16 | FR-001-20 | unit | `test_FR_001_20_record_case_change_never_logs_override_reason` | benefit-be:tests/apps/worker/activities/test_case_record.py |
| TC-17 | FR-001-13 | workflow | `test_FR_001_13_case_now_wf_uses_workflow_now` | benefit-be:tests/apps/worker/workflows/test_calendar.py |
| TC-18 | FR-001-04 | integration | `test_FR_001_04_record_case_change_retry_is_noop` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-19 | FR-001-10 | integration | `test_FR_001_10_case_change_writes_event_with_times_actor_reason` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-20 | FR-001-10 | integration | `test_FR_001_10_stale_seq_does_not_overwrite_case` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-21 | FR-001-20 | integration | `test_FR_001_20_override_outcome_stored_and_determination_unchanged` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-22 | FR-001-22 | integration | `test_FR_001_22_coverage_period_written_once_with_deterministic_id` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-23 | FR-001-04 | integration | `test_FR_001_04_failed_transaction_writes_nothing` | benefit-be:tests/apps/worker/repositories/test_cases.py |
| TC-24 | FR-001-23 | integration | `test_FR_001_23_partial_unique_index_allows_one_open_case_per_household` | benefit-be:tests/db/test_migrations.py |
| TC-25 | FR-001-01 | integration | `test_FR_001_01_submission_reference_is_unique` | benefit-be:tests/db/test_migrations.py |
| TC-26 | FR-001-04 | integration | `test_FR_001_04_case_events_case_id_seq_is_unique` | benefit-be:tests/db/test_migrations.py |
| TC-27 | FR-001-02 | integration | `test_FR_001_02_validator_rejects_unknown_case_state_and_outcome` | benefit-be:tests/db/test_migrations.py |
| TC-28 | FR-001-01 | integration | `test_FR_001_01_migration_0002_downgrade_restores_baseline_validators` | benefit-be:tests/db/test_migrations.py |
| TC-29 | FR-001-16 | integration | `test_FR_001_16_seed_covers_every_stub_result_with_synthetic_households` | benefit-be:tests/db/seeds/test_reset.py |
| TC-30 | FR-001-16 | workflow | `test_FR_001_16_eligible_decides_approved` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-31 | FR-001-09 | workflow | `test_FR_001_09_ineligible_waits_for_approve_denial` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-32 | FR-001-16 | workflow | `test_FR_001_16_cannot_determine_opens_task_never_decides` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-33 | FR-001-20 | workflow | `test_FR_001_20_override_keeps_determination` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-34 | FR-001-02 | workflow | `test_FR_001_02_disallowed_action_recorded_rejected` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-35 | FR-001-04 | workflow | `test_FR_001_04_duplicate_request_id_ignored` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-36 | FR-001-13 | workflow | `test_FR_001_13_events_carry_case_and_real_time` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-37 | FR-001-16 | workflow | `test_FR_001_16_income_and_other_rule_fail_denies_income_over_limit` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-38 | FR-001-07 | workflow | `test_FR_001_07_review_wait_holds_no_pending_activity` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-39 | FR-001-09 | workflow | `test_FR_001_09_ineligible_stays_under_review_past_deadline_without_action` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-40 | FR-001-20 | workflow | `test_FR_001_20_override_without_reason_recorded_rejected` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-41 | FR-001-07 | workflow | `test_FR_001_07_allowed_actions_query_lists_open_task_actions` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-42 | FR-001-02 | workflow | `test_FR_001_02_happy_path_visits_submitted_verifying_determining_decided` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-43 | FR-001-10 | workflow | `test_FR_001_10_every_state_change_recorded_with_actor_and_reason` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-44 | FR-001-11 | workflow | `test_FR_001_11_day_36_shows_9_remaining_at_risk` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-45 | FR-001-11 | workflow | `test_FR_001_11_decided_case_has_no_days_remaining` | benefit-be:tests/apps/worker/workflows/test_case.py |
| TC-46 | FR-001-03 | workflow | `test_FR_001_03_case_replay` | benefit-be:tests/apps/worker/workflows/test_case_replay.py |
| TC-47 | FR-001-03 | workflow | `test_FR_001_03_restart_mid_verification` | benefit-be:tests/apps/worker/workflows/test_case_restart.py |
| TC-48 | FR-001-03 | workflow | `test_FR_001_03_restart_while_waiting_on_task_no_second_task` | benefit-be:tests/apps/worker/workflows/test_case_restart.py |
| TC-49 | FR-001-04 | workflow | `test_FR_001_04_restart_after_approval_requests_no_second_notice` | benefit-be:tests/apps/worker/workflows/test_case_restart.py |
| TC-50 | FR-001-01 | unit | `test_FR_001_01_submit_opens_submitted_case_with_deadline_45_days` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-51 | FR-001-23 | unit | `test_FR_001_23_same_submission_twice_returns_existing_case` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-52 | FR-001-23 | unit | `test_FR_001_23_household_with_open_case_refused_with_reason` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-53 | FR-001-23 | unit | `test_FR_001_23_household_with_unended_coverage_refused` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-54 | FR-001-23 | unit | `test_FR_001_23_coverage_ended_yesterday_allows_new_application` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-55 | FR-001-01 | unit | `test_FR_001_01_temporal_down_returns_503_and_retry_starts_workflow` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-56 | FR-001-13 | unit | `test_FR_001_13_demo_profile_case_clock_scale_1440` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-57 | FR-001-23 | unit | `test_FR_001_23_household_taken_from_principal_not_body` | benefit-be:tests/apps/api/services/test_cases.py |
| TC-58 | FR-001-01 | unit | `test_FR_001_01_submit_application_rejects_non_applicant_roles` | benefit-be:tests/apps/api/routers/test_applications.py |
| TC-59 | FR-001-09 | unit | `test_FR_001_09_review_action_rejects_applicant_role` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-60 | FR-001-20 | unit | `test_FR_001_20_override_without_reason_returns_422` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-61 | FR-001-07 | unit | `test_FR_001_07_action_not_allowed_returns_409` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-62 | FR-001-07, FR-001-09 | unit | `test_FR_001_07_allowed_action_signals_with_principal_reviewer_returns_202` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-63 | FR-001-20 | unit | `test_FR_001_20_review_action_logs_no_reason_text` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-64 | FR-001-11 | unit | `test_FR_001_11_get_case_returns_days_remaining_and_at_risk` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-65 | FR-001-11 | unit | `test_FR_001_11_get_case_of_other_household_returns_404` | benefit-be:tests/apps/api/routers/test_cases.py |
| TC-66 | FR-001-01, FR-001-11, FR-001-23 | contract | `test_FR_001_01_openapi_matches_case_lifecycle_contract` | benefit-be:tests/contract/test_case_lifecycle_contract.py |
| TC-67 | FR-001-07 | contract | `test_FR_001_07_registered_workflow_names_match_contract` | benefit-be:tests/contract/test_case_lifecycle_contract.py |
| TC-68 | FR-001-23 | integration | `test_FR_001_23_concurrent_same_submission_opens_one_case_one_workflow` | benefit-be:tests/integration/test_case_submission.py |
| TC-69 | FR-001-23 | integration | `test_FR_001_23_concurrent_different_submissions_same_household_open_one` | benefit-be:tests/integration/test_case_submission.py |
| TC-70 | FR-001-10 | integration | `test_FR_001_10_audit_entry_commits_and_rolls_back_with_case_change` | benefit-be:tests/integration/test_case_audit.py |
| TC-71 | FR-001-01, FR-001-22 | integration | `test_FR_001_01_journey_submit_to_approved_with_coverage_and_notice` | benefit-be:tests/integration/test_case_journey.py |
| TC-72 | FR-001-09 | integration | `test_FR_001_09_journey_ineligible_approve_denial_decides_denied` | benefit-be:tests/integration/test_case_journey.py |
| TC-73 | FR-001-20 | integration | `test_FR_001_20_journey_override_to_approve_keeps_determination` | benefit-be:tests/integration/test_case_journey.py |
| TC-74 | FR-001-16 | integration | `test_FR_001_16_journey_cannot_determine_waits_on_task` | benefit-be:tests/integration/test_case_journey.py |
| TC-75 | FR-001-03, FR-001-04 | integration | `test_FR_001_03_journey_worker_restart_no_duplicate_effects` | benefit-be:tests/integration/test_case_restart.py |
| TC-76 | FR-001-11 | integration | `test_FR_001_11_api_status_matches_workflow_status_query` | benefit-be:tests/integration/test_case_journey.py |
| TC-77 | FR-001-13 | integration | `test_FR_001_13_demo_profile_history_has_case_and_real_times` | benefit-be:tests/integration/test_case_journey.py |
