# Requirement traceability

Mode: strict. A test counts only where it is defined (a Python `def`, a `test(`/`it(` title, or an eval case id) and not skipped.

| Case | Proves | Level | Test | Defined in |
|---|---|---|---|---|
| TC-01 | FR-003-01 | unit | `test_FR_003_01_household_meeting_every_rule_is_eligible` | benefit-be:tests/packages/rules/test_engine.py |
| TC-02 | FR-003-01 | unit | `test_FR_003_01_each_person_rule_fails_on_its_violation` | benefit-be:tests/packages/rules/test_checks.py |
| TC-03 | FR-003-01 | unit | `test_FR_003_01_age_evaluated_on_as_of_date_at_19_and_65_boundaries` | benefit-be:tests/packages/rules/test_checks.py |
| TC-04 | FR-003-01 | unit | `test_FR_003_01_age_rule_passes_iff_whole_years_in_19_to_64` | benefit-be:tests/packages/rules/test_checks.py |
| TC-05 | FR-003-02 | unit | `test_FR_003_02_result_is_always_eligible_ineligible_or_cannot_determine` | benefit-be:tests/packages/rules/test_engine.py |
| TC-06 | FR-003-02 | unit | `test_FR_003_02_eligibility_enums_and_determination_round_trip_json` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-07 | FR-003-02 | unit | `test_FR_003_02_determination_allows_no_rule_set` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-08 | FR-003-03 | unit | `test_FR_003_03_missing_fact_gives_cannot_determine_listing_item_not_ineligible` | benefit-be:tests/packages/rules/test_engine.py |
| TC-09 | FR-003-03 | unit | `test_FR_003_03_job_without_stub_is_missing_pay_stub` | benefit-be:tests/packages/rules/test_engine.py |
| TC-10 | FR-003-03 | unit | `test_FR_003_03_removing_information_from_eligible_household_never_gives_ineligible` | benefit-be:tests/packages/rules/test_engine.py |
| TC-11 | FR-003-04 | unit | `test_FR_003_04_same_snapshot_and_date_give_identical_determination_json` | benefit-be:tests/packages/rules/test_engine.py |
| TC-12 | FR-003-05 | unit | `test_FR_003_05_ineligible_result_names_every_failed_rule` | benefit-be:tests/packages/rules/test_engine.py |
| TC-13 | FR-003-05 | unit | `test_FR_003_05_income_ineligible_trace_shows_income_size_limit_year_and_policy_ref` | benefit-be:tests/packages/rules/test_engine.py |
| TC-14 | FR-003-05 | unit | `test_FR_003_05_trace_inputs_and_thresholds_per_rule` | benefit-be:tests/packages/rules/test_engine.py |
| TC-15 | FR-003-05 | unit | `test_FR_003_05_every_determination_has_six_complete_rule_results_in_id_order` | benefit-be:tests/packages/rules/test_engine.py |
| TC-16 | FR-003-05 | contract | `test_FR_003_05_eligibility_models_match_committed_schema` | benefit-be:tests/contract/test_eligibility_models.py |
| TC-17 | FR-003-05 | unit | `test_FR_003_05_stub_engine_returns_eligible_with_six_passing_rule_results` | benefit-be:tests/packages/rules/test_stub.py |
| TC-18 | FR-003-06 | unit | `test_FR_003_06_rule_sets_cover_2025_and_2026_without_gap_or_overlap` | benefit-be:tests/packages/rules/test_rule_sets.py |
| TC-19 | FR-003-06 | unit | `test_FR_003_06_rule_set_round_trips_and_rejects_other_state` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-20 | FR-003-07 | unit | `test_FR_003_07_as_of_date_in_2025_uses_2025_limit` | benefit-be:tests/packages/rules/test_engine.py |
| TC-21 | FR-003-07 | unit | `test_FR_003_07_date_without_rule_set_gives_cannot_determine_no_rules_for_date` | benefit-be:tests/packages/rules/test_engine.py |
| TC-22 | FR-003-07 | unit | `test_FR_003_07_dates_outside_every_rule_set_have_none` | benefit-be:tests/packages/rules/test_rule_sets.py |
| TC-23 | FR-003-07, FR-003-21 | unit | `test_FR_003_07_year_boundary_dates_select_their_calendar_year_rule_set` | benefit-be:tests/packages/rules/test_rule_sets.py |
| TC-24 | FR-003-08 | contract | `test_FR_003_08_rules_package_imports_no_io_clock_random_or_logging` | benefit-be:tests/contract/test_rules_purity.py |
| TC-25 | FR-003-08 | contract | `test_FR_003_08_rules_imported_only_by_worker_activities_seeds_and_evals` | benefit-be:tests/contract/test_rules_purity.py |
| TC-26 | FR-003-09 | unit | `test_FR_003_09_known_answer_case_matches_expected_result_failed_missing_income_limit` | benefit-be:tests/packages/rules/test_known_answers.py |
| TC-27 | FR-003-09 | unit | `test_FR_003_09_known_answers_have_30_cases_covering_every_rule_edge_case_and_year` | benefit-be:tests/packages/rules/test_known_answers.py |
| TC-28 | FR-003-15 | unit | `test_FR_003_15_monthly_limit_is_floor_of_138_percent_annual_over_12` | benefit-be:tests/packages/rules/test_income.py |
| TC-29 | FR-003-16 | unit | `test_FR_003_16_person_rules_use_applicant_only_and_no_self_is_missing_applicant` | benefit-be:tests/packages/rules/test_checks.py |
| TC-30 | FR-003-16 | unit | `test_FR_003_16_missing_fact_results_carry_member_id_and_item` | benefit-be:tests/packages/rules/test_checks.py |
| TC-31 | FR-003-16 | unit | `test_FR_003_16_no_self_member_is_cannot_determine_with_applicant_missing` | benefit-be:tests/packages/rules/test_engine.py |
| TC-32 | FR-003-16 | unit | `test_FR_003_16_stored_member_keeps_unanswered_facts_as_none` | benefit-be:tests/packages/domain/test_household.py |
| TC-33 | FR-003-17 | unit | `test_FR_003_17_household_income_sums_all_members_and_all_jobs` | benefit-be:tests/packages/rules/test_income.py |
| TC-34 | FR-003-17 | unit | `test_FR_003_17_zero_declared_counts_zero_and_job_without_stub_is_missing` | benefit-be:tests/packages/rules/test_income.py |
| TC-35 | FR-003-17 | unit | `test_FR_003_17_job_income_allows_empty_stub_list` | benefit-be:tests/packages/domain/test_household.py |
| TC-36 | FR-003-17 | unit | `test_FR_003_17_pay_stub_rejects_negative_gross_and_money_serialises_as_string` | benefit-be:tests/packages/domain/test_household.py |
| TC-37 | FR-003-18 | unit | `test_FR_003_18_stub_converts_to_monthly_by_frequency_using_latest_stub` | benefit-be:tests/packages/rules/test_income.py |
| TC-38 | FR-003-18 | unit | `test_FR_003_18_latest_pay_date_wins_within_a_job` | benefit-be:tests/packages/rules/test_income.py |
| TC-39 | FR-003-18 | unit | `test_FR_003_18_monthly_income_is_non_negative_decimal_with_two_places` | benefit-be:tests/packages/rules/test_income.py |
| TC-40 | FR-003-19 | unit | `test_FR_003_19_household_snapshot_is_frozen_and_member_facts_have_no_names` | benefit-be:tests/packages/domain/test_household.py |
| TC-41 | FR-003-19 | unit | `test_FR_003_19_snapshot_round_trips_through_json` | benefit-be:tests/packages/domain/test_household.py |
| TC-42 | FR-003-19 | unit | `test_FR_003_19_size_is_member_count_and_captured_at_does_not_change_result` | benefit-be:tests/packages/rules/test_engine.py |
| TC-43 | FR-003-19 | unit | `test_FR_003_19_determination_record_wraps_engine_output` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-44 | FR-003-20 | unit | `test_FR_003_20_failed_rule_plus_missing_info_is_ineligible_listing_missing_item` | benefit-be:tests/packages/rules/test_engine.py |
| TC-45 | FR-003-20 | unit | `test_FR_003_20_result_follows_fail_then_missing_then_eligible_precedence` | benefit-be:tests/packages/rules/test_engine.py |
| TC-46 | FR-003-10 | unit | `test_FR_003_10_dataset_metadata_requires_anchor_date_and_synthetic_true` | benefit-be:tests/packages/domain/test_dataset.py |
| TC-47 | FR-003-10 | integration | `test_FR_003_10_same_seed_gives_identical_dataset` | benefit-be:tests/db/seeds/test_documents.py |
| TC-48 | FR-003-10 | integration | `test_FR_003_10_dataset_has_200_households_two_years_sizes_1_to_6_and_60pct_under_limit` | benefit-be:tests/db/seeds/test_households.py |
| TC-49 | FR-003-10 | integration | `test_FR_003_10_other_anchor_shifts_only_dates_and_default_anchor_is_2026_11_10` | benefit-be:tests/db/seeds/test_households.py |
| TC-50 | FR-003-10 | integration | `test_FR_003_10_members_are_adults_19_to_64_for_applicants_in_both_years` | benefit-be:tests/db/seeds/test_households.py |
| TC-51 | FR-003-10 | integration | `test_FR_003_10_meta_records_synthetic_seed_and_anchor_date` | benefit-be:tests/db/seeds/test_reset.py |
| TC-52 | FR-003-11 | integration | `test_FR_003_11_income_mismatches_within_15pct_and_special_households_present` | benefit-be:tests/db/seeds/test_households.py |
| TC-53 | FR-003-12 | integration | `test_FR_003_12_every_generated_document_carries_synthetic_marker` | benefit-be:tests/db/seeds/test_documents.py |
| TC-54 | FR-003-12 | integration | `test_FR_003_12_pay_stubs_cover_three_frequencies_with_10pct_poor_quality` | benefit-be:tests/db/seeds/test_documents.py |
| TC-55 | FR-003-13 | integration | `test_FR_003_13_consumer_lanes_load_testsets_with_domain_models` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-56 | FR-003-14 | integration | `test_FR_003_14_demo_users_link_to_their_scenario_households` | benefit-be:tests/db/seeds/test_households.py |
| TC-57 | FR-003-16 | integration | `test_FR_003_16_seeded_members_carry_attested_residency_citizenship_and_medicare` | benefit-be:tests/db/seeds/test_households.py |
| TC-58 | FR-003-06 | integration | `test_FR_003_06_reset_mirrors_both_rule_sets_into_collection` | benefit-be:tests/db/seeds/test_reset.py |
| TC-59 | FR-003-22 | integration | `test_FR_003_22_every_seeded_row_passes_its_owning_collection_validator` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-60 | FR-003-22 | contract | `test_FR_003_22_seeds_never_read_wall_clock` | benefit-be:tests/contract/test_rules_purity.py |
| TC-61 | FR-003-04 | unit | `test_FR_003_04_property_same_inputs_give_equal_determination` | benefit-be:tests/packages/rules/test_properties.py |
| TC-62 | FR-003-01 | unit | `test_FR_003_01_property_income_at_or_below_limit_passes_income_rule` | benefit-be:tests/packages/rules/test_properties.py |
| TC-63 | FR-003-20 | unit | `test_FR_003_20_property_any_fail_gives_ineligible_and_missing_only_gives_cannot_determine` | benefit-be:tests/packages/rules/test_properties.py |
| TC-64 | FR-003-08 | unit | `test_FR_003_08_property_evaluate_leaves_snapshot_unchanged` | benefit-be:tests/packages/rules/test_properties.py |
| TC-65 | FR-003-06 | unit | `test_FR_003_06_seeded_rule_set_documents_equal_RULE_SETS` | benefit-be:tests/packages/rules/test_rule_sets.py |
| TC-66 | FR-003-07 | unit | `test_FR_003_07_same_household_as_of_2025_and_2026_uses_each_years_limit` | benefit-be:tests/packages/rules/test_rule_sets.py |
| TC-67 | FR-003-05 | unit | `test_FR_003_05_stub_policy_refs_are_the_engine_policy_refs` | benefit-be:tests/packages/rules/test_stub.py |
| TC-68 | FR-003-02 | unit | `test_FR_003_02_eligibility_reuses_main_outcome_pay_frequency_and_relationship` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-69 | FR-003-23 | unit | `test_FR_003_23_determination_view_has_contract_fields_and_forbids_extra` | benefit-be:tests/packages/domain/test_eligibility.py |
| TC-70 | FR-003-17 | unit | `test_FR_003_17_verified_member_facts_round_trips_and_forbids_extra` | benefit-be:tests/packages/domain/test_household.py |
| TC-71 | FR-003-19 | unit | `test_FR_003_19_snapshot_requires_as_of_date` | benefit-be:tests/packages/domain/test_household.py |
| TC-72 | FR-003-06 | integration | `test_FR_003_06_migration_0005_upgrade_enforces_validators_and_downgrade_restores_0004` | benefit-be:tests/db/migrations/test_0005_eligibility.py |
| TC-73 | FR-003-19 | integration | `test_FR_003_19_migration_0005_rejects_second_snapshot_for_same_case_and_date` | benefit-be:tests/db/migrations/test_0005_eligibility.py |
| TC-74 | FR-003-16 | integration | `test_FR_003_16_migration_0005_creates_seeded_verifications_unique_per_member` | benefit-be:tests/db/migrations/test_0005_eligibility.py |
| TC-75 | FR-003-14 | integration | `test_FR_003_14_demo_households_evaluate_eligible_ineligible_income_cannot_determine` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-76 | FR-003-14 | integration | `test_FR_003_14_demo_households_have_no_open_case_or_current_coverage` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-77 | FR-003-16, FR-003-17 | integration | `test_FR_003_16_every_seeded_member_has_one_verification_with_identity_and_stub_facts` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-78 | FR-003-13 | integration | `test_FR_003_13_pay_stub_extractions_has_10_to_20_stubs_with_expected_values` | benefit-be:tests/db/seeds/test_test_sets.py |
| TC-79 | FR-003-13 | integration | `test_FR_003_13_redeterminations_due_lists_households_due_in_demo_window` | benefit-be:tests/db/seeds/test_test_sets.py |
| TC-80 | FR-003-13 | integration | `test_FR_003_13_expected_metrics_match_values_recomputed_from_seeded_history` | benefit-be:tests/db/seeds/test_test_sets.py |
| TC-81 | FR-003-10 | integration | `test_FR_003_10_manifest_hashes_identical_across_two_runs_with_same_seed` | benefit-be:tests/db/seeds/test_test_sets.py |
| TC-82 | FR-003-22 | integration | `test_FR_003_22_history_has_decided_2025_and_current_period_cases_with_all_records` | benefit-be:tests/db/seeds/test_history.py |
| TC-83 | FR-003-22 | integration | `test_FR_003_22_collection_counts_match_manifest_after_reset` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-84 | FR-003-22 | integration | `test_FR_003_22_history_files_reference_existing_determinations_and_cases` | benefit-be:tests/db/seeds/test_history.py |
| TC-85 | FR-003-12 | integration | `test_FR_003_12_every_seeded_record_in_every_collection_is_marked_synthetic` | benefit-be:tests/integration/test_seeded_dataset.py |
| TC-86 | FR-003-16 | integration | `test_FR_003_16_seeded_verified_facts_returns_only_the_scoped_households_members` | benefit-be:tests/integration/worker/test_worker_stores.py |
| TC-87 | FR-003-19 | integration | `test_FR_003_19_snapshot_insert_twice_keeps_one_document` | benefit-be:tests/integration/worker/test_worker_stores.py |
| TC-88 | FR-003-04 | integration | `test_FR_003_04_determination_insert_duplicate_key_is_treated_as_done` | benefit-be:tests/integration/worker/test_worker_stores.py |
| TC-89 | FR-003-19 | unit | `test_FR_003_19_existing_snapshot_for_case_and_date_is_reused` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-90 | FR-003-19, FR-003-21 | unit | `test_FR_003_19_snapshot_uses_members_of_the_as_of_year` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-91 | FR-003-16 | unit | `test_FR_003_16_snapshot_from_application_form_maps_attested_facts_and_leaves_identity_unknown` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-92 | FR-003-03 | unit | `test_FR_003_03_form_job_without_verified_stub_gives_cannot_determine_not_ineligible` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-93 | FR-003-17 | unit | `test_FR_003_17_verified_facts_merged_into_member_jobs_and_identity` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-94 | FR-003-19 | unit | `test_FR_003_19_captured_snapshot_contains_no_member_names` | benefit-be:tests/apps/worker/activities/test_snapshot.py |
| TC-95 | FR-003-04 | unit | `test_FR_003_04_same_request_twice_stores_one_record_and_returns_identical_summary` | benefit-be:tests/apps/worker/activities/test_determination.py |
| TC-96 | FR-003-19 | unit | `test_FR_003_19_member_change_after_capture_does_not_change_determination` | benefit-be:tests/apps/worker/activities/test_determination.py |
| TC-97 | FR-003-02 | unit | `test_FR_003_02_summary_maps_each_outcome_to_reason_failed_rules_and_missing_items` | benefit-be:tests/apps/worker/activities/test_determination.py |
| TC-98 | FR-003-02 | unit | `test_FR_003_02_determination_id_matches_stub_formula` | benefit-be:tests/apps/worker/activities/test_determination.py |
| TC-99 | FR-003-02 | workflow | `test_FR_003_02_real_determination_store_failing_past_retries_opens_review_and_does_not_stall` | benefit-be:tests/apps/worker/workflows/test_determination_failures.py |
| TC-100 | FR-001-03 | workflow | `test_FR_001_03_case_replay` | benefit-be:tests/apps/worker/workflows/test_case_replay.py |
| TC-101 | FR-010-01 | workflow | `test_FR_010_01_review_history_replays_without_nondeterminism` | benefit-be:tests/apps/worker/workflows/test_review_replay.py |
| TC-102 | FR-003-16 | integration | `test_FR_003_16_worker_scope_cannot_read_another_households_seeded_verifications` | benefit-be:tests/db/test_scope.py |
| TC-103 | FR-003-23 | unit | `test_FR_003_23_caseworker_gets_determinations_newest_first_with_reason_code` | benefit-be:tests/apps/api/test_determinations.py |
| TC-104 | FR-003-23 | unit | `test_FR_003_23_supervisor_can_read_case_determinations` | benefit-be:tests/apps/api/test_determinations.py |
| TC-105 | FR-003-23 | unit | `test_FR_003_23_applicant_gets_403_error_envelope` | benefit-be:tests/apps/api/test_determinations.py |
| TC-106 | FR-003-23 | unit | `test_FR_003_23_applicant_refusal_is_audited` | benefit-be:tests/apps/api/test_determinations.py |
| TC-107 | FR-003-23 | unit | `test_FR_003_23_unauthenticated_gets_401_error_envelope` | benefit-be:tests/apps/api/test_determinations.py |
| TC-108 | FR-003-23 | unit | `test_FR_003_23_unknown_case_gets_404_error_envelope` | benefit-be:tests/apps/api/test_determinations.py |
| TC-109 | FR-003-23 | unit | `test_FR_003_23_non_uuid_case_id_gets_422_error_envelope` | benefit-be:tests/apps/api/test_determinations.py |
| TC-110 | FR-003-23 | unit | `test_FR_003_23_case_without_determination_returns_empty_list` | benefit-be:tests/apps/api/test_determinations.py |
| TC-111 | FR-003-23 | unit | `test_FR_003_23_cannot_determine_view_lists_missing_items_and_null_reason` | benefit-be:tests/apps/api/test_determinations.py |
| TC-112 | FR-003-05 | unit | `test_FR_003_05_api_rule_inputs_carry_member_ids_never_names` | benefit-be:tests/apps/api/test_determinations.py |
| TC-113 | FR-003-23 | unit | `test_FR_003_23_determination_read_writes_audit_entry` | benefit-be:tests/apps/api/test_determinations.py |
| TC-114 | FR-003-23 | integration | `test_FR_003_23_repository_reads_case_determinations_by_recorded_at_desc_max_20` | benefit-be:tests/integration/api/test_determinations_repository.py |
| TC-115 | FR-003-23 | contract | `test_FR_003_23_committed_openapi_has_list_case_determinations_matching_contract` | benefit-be:tests/contract/test_openapi_determinations.py |
| TC-116 | FR-003-23 | unit | `FR-003-23: fetches determinations under key cases/id/determinations when a case id is given` | benefit-fe:src/api/determinations.test.ts |
| TC-117 | FR-003-23 | contract | `FR-003-23: generated schema types listCaseDeterminations as DeterminationList` | benefit-fe:src/api/generated.test.ts |
| TC-118 | FR-003-23 | unit | `FR-003-23: shows result, reason code, as-of date and rule set version when the case is determined` | benefit-fe:src/features/caseworker/case-page/DeterminationSection.test.tsx |
| TC-119 | FR-003-23, FR-003-05 | unit | `FR-003-23: lists each rule's ID, inputs, threshold and outcome when the determination has six rules` | benefit-fe:src/features/caseworker/case-page/DeterminationSection.test.tsx |
| TC-120 | FR-003-23 | unit | `FR-003-23: lists the missing items when the result is cannot determine` | benefit-fe:src/features/caseworker/case-page/DeterminationSection.test.tsx |
| TC-121 | FR-003-23 | unit | `FR-003-23: shows an empty state when the case has no determination` | benefit-fe:src/features/caseworker/case-page/DeterminationSection.test.tsx |
| TC-122 | FR-003-23 | unit | `FR-003-23: shows the error state when the determinations request fails` | benefit-fe:src/features/caseworker/case-page/DeterminationSection.test.tsx |
| TC-123 | FR-003-23 | unit | `FR-003-23: case page renders the determination section when it is registered` | benefit-fe:src/features/caseworker/case-page/sections.test.tsx |
| TC-124 | FR-003-23 | e2e | `FR-003-23: caseworker sees demo household A's eligible determination with six passing rules matching the API` | benefit-fe:e2e/caseworker-sees-determination.spec.ts |
| TC-125 | FR-003-23 | e2e | `FR-003-23: caseworker sees demo household B ineligible with reason income over limit and ELIG-06 failed` | benefit-fe:e2e/caseworker-sees-determination.spec.ts |
| TC-126 | FR-003-23 | e2e | `FR-003-23: caseworker sees the missing pay stub when demo household C cannot be determined` | benefit-fe:e2e/caseworker-sees-determination.spec.ts |
| TC-127 | FR-003-23 | e2e | `FR-003-23: determination section has no axe violations` | benefit-fe:e2e/caseworker-sees-determination.spec.ts |
| TC-128 | FR-003-23 | e2e | `FR-003-23: caseworker sees a seeded 2025 history determination with the 2025 rule set version` | benefit-fe:e2e/caseworker-sees-determination.spec.ts |
| TC-129 | FR-003-14, FR-003-02 | integration | `test_FR_003_14_seeded_households_a_b_c_submit_form_and_end_eligible_ineligible_cannot_determine` | benefit-be:tests/integration/test_determination_journey.py |
| TC-130 | FR-003-23, FR-003-19 | integration | `test_FR_003_23_determination_stored_by_workflow_is_readable_through_api` | benefit-be:tests/integration/test_determination_journey.py |
| TC-131 | FR-003-05, FR-003-13, FR-003-22 | integration | `test_FR_003_05_every_seeded_history_and_test_set_determination_has_six_rule_trace` | benefit-be:tests/integration/test_determination_traces.py |
