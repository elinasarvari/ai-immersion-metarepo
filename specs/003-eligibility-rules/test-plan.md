# Test plan: 003-eligibility-rules

Sources: spec.md (FR-003-01…23, US1–US5, edge cases, SC-003-01…04), plan.md, data-model.md, contracts/, ADR-003-01…06, research R5/R6/R8/R11/R12, quickstart.md. TC-01…TC-60 are tests already on the branch (research R0), kept by name; TC-61 onwards are new. Levels per testing.md and the lane rules: unit = pure rules and models (KD-3, BA-11), integration = MongoDB through repositories and seeds (KD-16, PL-7), workflow = Temporal test environment and replay (TW-13, TW-14), contract = models ↔ OpenAPI ↔ client (KD-8 snapshots, FE-3), e2e = Playwright journey with axe (FE-12). All data is synthetic, from `db/seeds` with the fixed seed (PR-3, BA-11); no model calls (FR-000-20). `tests/db/` and `tests/integration/` need MongoDB, so their cases are integration.

Seed names used below: **A/B/C** = demo households from T015 (A eligible, B income over the limit, C a declared job without a usable stub), each with no open case. **KA-n** = known-answer case n in `known_answers.json`. **H-ineligible-2025** etc. = a seeded history case found by `seeded_id` in `db/seeds/generated/history/`.

## Cases

| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-003-01, US1-AS1 | unit | data-lane / benefit-be | test_FR_003_01_household_meeting_every_rule_is_eligible | snapshot: 1 adult 30, IL, citizen, identity verified, no Medicare, income under limit |
| TC-02 | FR-003-01 | unit | data-lane / benefit-be | test_FR_003_01_each_person_rule_fails_on_its_violation | parametrized: one violation each of ELIG-01…05 on an otherwise eligible snapshot |
| TC-03 | FR-003-01, edge "turns 19 or 65" | unit | data-lane / benefit-be | test_FR_003_01_age_evaluated_on_as_of_date_at_19_and_65_boundaries | DOBs one day before/on/after the 19th and 65th birthdays relative to as-of date |
| TC-04 | FR-003-01 | unit | data-lane / benefit-be | test_FR_003_01_age_rule_passes_iff_whole_years_in_19_to_64 | hypothesis DOBs (KD-3) |
| TC-05 | FR-003-02 | unit | data-lane / benefit-be | test_FR_003_02_result_is_always_eligible_ineligible_or_cannot_determine | hypothesis snapshots |
| TC-06 | FR-003-02, ADR-003-04 | unit | contracts / benefit-be | test_FR_003_02_eligibility_enums_and_determination_round_trip_json | engine Determination with each `DeterminationOutcome` (after T001: main's enum) |
| TC-07 | FR-003-02 | unit | contracts / benefit-be | test_FR_003_02_determination_allows_no_rule_set | Determination with `rule_set_id=None` (no rules for date) |
| TC-08 | FR-003-03, US1-AS3 | unit | data-lane / benefit-be | test_FR_003_03_missing_fact_gives_cannot_determine_listing_item_not_ineligible | eligible snapshot with one attested fact `None` per rule |
| TC-09 | FR-003-03 | unit | data-lane / benefit-be | test_FR_003_03_job_without_stub_is_missing_pay_stub | member with a declared job and empty stub list |
| TC-10 | FR-003-03 | unit | data-lane / benefit-be | test_FR_003_03_removing_information_from_eligible_household_never_gives_ineligible | hypothesis: eligible snapshot with random facts removed |
| TC-11 | FR-003-04, US1-AS4 | unit | data-lane / benefit-be | test_FR_003_04_same_snapshot_and_date_give_identical_determination_json | any known-answer snapshot evaluated twice |
| TC-12 | FR-003-05, US1-AS2 | unit | data-lane / benefit-be | test_FR_003_05_ineligible_result_names_every_failed_rule | snapshot failing ELIG-01 and ELIG-06 |
| TC-13 | FR-003-05, US2-AS1 | unit | data-lane / benefit-be | test_FR_003_05_income_ineligible_trace_shows_income_size_limit_year_and_policy_ref | 3-person household, income $1 over the 2026 limit |
| TC-14 | FR-003-05 | unit | data-lane / benefit-be | test_FR_003_05_trace_inputs_and_thresholds_per_rule | eligible snapshot; expected inputs/threshold per rule |
| TC-15 | FR-003-05, SC-003-02 | unit | data-lane / benefit-be | test_FR_003_05_every_determination_has_six_complete_rule_results_in_id_order | hypothesis snapshots, including no rule set |
| TC-16 | FR-003-05, KD-8 | contract | contracts / benefit-be | test_FR_003_05_eligibility_models_match_committed_schema | `tests/contract/snapshots/eligibility_models.json` (refreshed by T002) |
| TC-17 | FR-003-05 | unit | data-lane / benefit-be | test_FR_003_05_stub_engine_returns_eligible_with_six_passing_rule_results | any snapshot through `StubRulesEngine` |
| TC-18 | FR-003-06 | unit | data-lane / benefit-be | test_FR_003_06_rule_sets_cover_2025_and_2026_without_gap_or_overlap | `RULE_SETS` |
| TC-19 | FR-003-06 | unit | contracts / benefit-be | test_FR_003_06_rule_set_round_trips_and_rejects_other_state | RuleSet with state "IL" and one with another state |
| TC-20 | FR-003-07, US3-AS1 | unit | data-lane / benefit-be | test_FR_003_07_as_of_date_in_2025_uses_2025_limit | 1 person, as-of 2025-06-01: limit $1,725 |
| TC-21 | FR-003-07, edge "no rule set" | unit | data-lane / benefit-be | test_FR_003_07_date_without_rule_set_gives_cannot_determine_no_rules_for_date | as-of 2024-12-31 and 2027-01-01 |
| TC-22 | FR-003-07 | unit | data-lane / benefit-be | test_FR_003_07_dates_outside_every_rule_set_have_none | hypothesis dates outside 2025–2026 |
| TC-23 | FR-003-07, FR-003-21 | unit | data-lane / benefit-be | test_FR_003_07_year_boundary_dates_select_their_calendar_year_rule_set | 2025-12-31, 2026-01-01 |
| TC-24 | FR-003-08, ADR-003-01 | contract | data-lane / benefit-be | test_FR_003_08_rules_package_imports_no_io_clock_random_or_logging | AST of `packages/rules` |
| TC-25 | FR-003-08, BA-4 | contract | data-lane / benefit-be | test_FR_003_08_rules_imported_only_by_worker_activities_seeds_and_evals | AST of the repo |
| TC-26 | FR-003-09, SC-003-01 | unit | data-lane / benefit-be | test_FR_003_09_known_answer_case_matches_expected_result_failed_missing_income_limit | every KA-n, parametrized |
| TC-27 | FR-003-09 | unit | data-lane / benefit-be | test_FR_003_09_known_answers_have_30_cases_covering_every_rule_edge_case_and_year | `known_answers.json` tags: every rule, every edge case, 2025 and 2026 |
| TC-28 | FR-003-15 | unit | data-lane / benefit-be | test_FR_003_15_monthly_limit_is_floor_of_138_percent_annual_over_12 | sizes 1–6 × 2025/2026; 1 person 2026 = $1,782 |
| TC-29 | FR-003-16 | unit | data-lane / benefit-be | test_FR_003_16_person_rules_use_applicant_only_and_no_self_is_missing_applicant | household with an ineligible non-applicant spouse |
| TC-30 | FR-003-16 | unit | data-lane / benefit-be | test_FR_003_16_missing_fact_results_carry_member_id_and_item | applicant with `medicare_entitled=None` |
| TC-31 | FR-003-16 | unit | data-lane / benefit-be | test_FR_003_16_no_self_member_is_cannot_determine_with_applicant_missing | snapshot without a `self` member |
| TC-32 | FR-003-16 | unit | contracts / benefit-be | test_FR_003_16_stored_member_keeps_unanswered_facts_as_none | HouseholdMember with unanswered attestations |
| TC-33 | FR-003-17 | unit | data-lane / benefit-be | test_FR_003_17_household_income_sums_all_members_and_all_jobs | 2 earners, 3 jobs |
| TC-34 | FR-003-17, edge "zero income" | unit | data-lane / benefit-be | test_FR_003_17_zero_declared_counts_zero_and_job_without_stub_is_missing | member declaring zero income; member with stub-less job |
| TC-35 | FR-003-17 | unit | contracts / benefit-be | test_FR_003_17_job_income_allows_empty_stub_list | JobIncome with `stubs=[]` |
| TC-36 | FR-003-17 | unit | contracts / benefit-be | test_FR_003_17_pay_stub_rejects_negative_gross_and_money_serialises_as_string | PayStubFact gross −1 and 1234.50 |
| TC-37 | FR-003-18, edge "weekly $400" | unit | data-lane / benefit-be | test_FR_003_18_stub_converts_to_monthly_by_frequency_using_latest_stub | weekly $400 → $1,733.33; bi-weekly, semi-monthly, monthly |
| TC-38 | FR-003-18 | unit | data-lane / benefit-be | test_FR_003_18_latest_pay_date_wins_within_a_job | one job, stubs on 3 pay dates |
| TC-39 | FR-003-18 | unit | data-lane / benefit-be | test_FR_003_18_monthly_income_is_non_negative_decimal_with_two_places | hypothesis gross pay |
| TC-40 | FR-003-19, VIII | unit | contracts / benefit-be | test_FR_003_19_household_snapshot_is_frozen_and_member_facts_have_no_names | HouseholdSnapshot; MemberFacts field set |
| TC-41 | FR-003-19 | unit | contracts / benefit-be | test_FR_003_19_snapshot_round_trips_through_json | snapshot with 3 members |
| TC-42 | FR-003-19 | unit | data-lane / benefit-be | test_FR_003_19_size_is_member_count_and_captured_at_does_not_change_result | same snapshot, two `captured_at` values |
| TC-43 | FR-003-19 | unit | contracts / benefit-be | test_FR_003_19_determination_record_wraps_engine_output | DeterminationRecord around an engine Determination |
| TC-44 | FR-003-20, edge "one fails, one missing" | unit | data-lane / benefit-be | test_FR_003_20_failed_rule_plus_missing_info_is_ineligible_listing_missing_item | ELIG-01 fails, ELIG-04 missing |
| TC-45 | FR-003-20 | unit | data-lane / benefit-be | test_FR_003_20_result_follows_fail_then_missing_then_eligible_precedence | parametrized outcome combinations |
| TC-46 | FR-003-10 | unit | contracts / benefit-be | test_FR_003_10_dataset_metadata_requires_anchor_date_and_synthetic_true | dataset metadata model |
| TC-47 | FR-003-10, US4-AS1, SC-003-03 | integration | data-lane / benefit-be | test_FR_003_10_same_seed_gives_identical_dataset | generator run twice, fixed seed, two tmp dirs |
| TC-48 | FR-003-10 | integration | data-lane / benefit-be | test_FR_003_10_dataset_has_200_households_two_years_sizes_1_to_6_and_60pct_under_limit | generated data set |
| TC-49 | FR-003-10 | integration | data-lane / benefit-be | test_FR_003_10_other_anchor_shifts_only_dates_and_default_anchor_is_2026_11_10 | anchors 2026-11-10 and another date |
| TC-50 | FR-003-10 | integration | data-lane / benefit-be | test_FR_003_10_members_are_adults_19_to_64_for_applicants_in_both_years | generated data set |
| TC-51 | FR-003-10 | integration | data-lane / benefit-be | test_FR_003_10_meta_records_synthetic_seed_and_anchor_date | `_meta` after reset |
| TC-52 | FR-003-11 | integration | data-lane / benefit-be | test_FR_003_11_income_mismatches_within_15pct_and_special_households_present | generated data set |
| TC-53 | FR-003-12, US4-AS2 | integration | data-lane / benefit-be | test_FR_003_12_every_generated_document_carries_synthetic_marker | every generated PDF/PNG |
| TC-54 | FR-003-12 | integration | data-lane / benefit-be | test_FR_003_12_pay_stubs_cover_three_frequencies_with_10pct_poor_quality | generated stubs |
| TC-55 | FR-003-13, SC-003-04 | integration | data-lane / benefit-be | test_FR_003_13_consumer_lanes_load_testsets_with_domain_models | every file in `db/seeds/generated/` |
| TC-56 | FR-003-14 | integration | data-lane / benefit-be | test_FR_003_14_demo_users_link_to_their_scenario_households | 000's demo users → A/B/C |
| TC-57 | FR-003-16 | integration | data-lane / benefit-be | test_FR_003_16_seeded_members_carry_attested_residency_citizenship_and_medicare | seeded `household_members` |
| TC-58 | FR-003-06, ADR-003-01 | integration | data-lane / benefit-be | test_FR_003_06_reset_mirrors_both_rule_sets_into_collection | `rule_sets` after reset |
| TC-59 | FR-003-22, ADR-003-06 | integration | data-lane / benefit-be | test_FR_003_22_every_seeded_row_passes_its_owning_collection_validator | every seeded collection after reset (incl. history) |
| TC-60 | FR-003-22 | contract | data-lane / benefit-be | test_FR_003_22_seeds_never_read_wall_clock | AST of `db/seeds` |
| TC-61 | FR-003-04 | unit | data-lane / benefit-be | test_FR_003_04_property_same_inputs_give_equal_determination | hypothesis snapshots and dates (KD-3, T008) |
| TC-62 | FR-003-01, edge "income exactly at the limit" | unit | data-lane / benefit-be | test_FR_003_01_property_income_at_or_below_limit_passes_income_rule | hypothesis sizes 1–6 × year; income = limit, limit − 0.01, limit + 0.01 |
| TC-63 | FR-003-20 | unit | data-lane / benefit-be | test_FR_003_20_property_any_fail_gives_ineligible_and_missing_only_gives_cannot_determine | hypothesis snapshots with injected fails/missing |
| TC-64 | FR-003-08 | unit | data-lane / benefit-be | test_FR_003_08_property_evaluate_leaves_snapshot_unchanged | hypothesis snapshots; compare JSON before/after |
| TC-65 | FR-003-06, ADR-003-01 | unit | data-lane / benefit-be | test_FR_003_06_seeded_rule_set_documents_equal_RULE_SETS | documents the seed writes to `rule_sets` vs `RULE_SETS` (T009) |
| TC-66 | FR-003-07, US3-AS1 | unit | data-lane / benefit-be | test_FR_003_07_same_household_as_of_2025_and_2026_uses_each_years_limit | 2-person household, income $2,350, as-of 2025-07-01 and 2026-07-01: Ineligible under the $2,300 limit, Eligible under the $2,380 limit; the trace names each year's limit |
| TC-67 | FR-003-05, ADR-003-01 | unit | data-lane / benefit-be | test_FR_003_05_stub_policy_refs_are_the_engine_policy_refs | `StubRulesEngine` rule results vs `POLICY_REFS` (T010) |
| TC-68 | FR-003-02, ADR-003-04 | unit | contracts / benefit-be | test_FR_003_02_eligibility_reuses_main_outcome_pay_frequency_and_relationship | `packages.domain` has no `EligibilityResult`, one `PayFrequency`, one `Relationship` (8 values) (T001, T002) |
| TC-69 | FR-003-23, ADR-003-05 | unit | contracts / benefit-be | test_FR_003_23_determination_view_has_contract_fields_and_forbids_extra | DeterminationView field set vs `rest-api.openapi.yaml`; extra field rejected |
| TC-70 | FR-003-17, ADR-003-03 | unit | contracts / benefit-be | test_FR_003_17_verified_member_facts_round_trips_and_forbids_extra | VerifiedMemberFacts with 2 jobs; extra field rejected |
| TC-71 | FR-003-19 | unit | contracts / benefit-be | test_FR_003_19_snapshot_requires_as_of_date | HouseholdSnapshot without `as_of_date` rejected |
| TC-72 | FR-003-06, ADR-003-04 | integration | data-lane / benefit-be | test_FR_003_06_migration_0005_upgrade_enforces_validators_and_downgrade_restores_0004 | DB at 0004; upgrade, invalid docs rejected; downgrade recreates `household_stub_results` (T011) |
| TC-73 | FR-003-19, ADR-003-03 | integration | data-lane / benefit-be | test_FR_003_19_migration_0005_rejects_second_snapshot_for_same_case_and_date | two snapshots with same `(case_id, as_of_date)` |
| TC-74 | FR-003-16, ADR-003-03 | integration | data-lane / benefit-be | test_FR_003_16_migration_0005_creates_seeded_verifications_unique_per_member | duplicate `(household_id, member_id)` rejected |
| TC-75 | FR-003-14, ADR-003-03 | integration | data-lane / benefit-be | test_FR_003_14_demo_households_evaluate_eligible_ineligible_income_cannot_determine | seeded A/B/C members + seeded verifications through `evaluate` as of the anchor date (T015) |
| TC-76 | FR-003-14, ADR-003-06 | integration | data-lane / benefit-be | test_FR_003_14_demo_households_have_no_open_case_or_current_coverage | after reset: no case, coverage period or history for A/B/C |
| TC-77 | FR-003-16, FR-003-17 | integration | data-lane / benefit-be | test_FR_003_16_every_seeded_member_has_one_verification_with_identity_and_stub_facts | `seeded_verifications` vs seeded members and jobs; C's job has no stub (T016) |
| TC-78 | FR-003-13 | integration | data-lane / benefit-be | test_FR_003_13_pay_stub_extractions_has_10_to_20_stubs_with_expected_values | `pay_stub_extractions.json` vs generated stub documents (T017) |
| TC-79 | FR-003-13 | integration | data-lane / benefit-be | test_FR_003_13_redeterminations_due_lists_households_due_in_demo_window | `redeterminations_due.json` vs seeded coverage periods ending in the demo window |
| TC-80 | FR-003-13 | integration | data-lane / benefit-be | test_FR_003_13_expected_metrics_match_values_recomputed_from_seeded_history | `expected_metrics.json` vs counts recomputed from seeded cases |
| TC-81 | FR-003-10, SC-003-03 | integration | data-lane / benefit-be | test_FR_003_10_manifest_hashes_identical_across_two_runs_with_same_seed | `manifest.json` from two runs (quickstart 3) |
| TC-82 | FR-003-22, ADR-003-06 | integration | data-lane / benefit-be | test_FR_003_22_history_has_decided_2025_and_current_period_cases_with_all_records | after reset: each history case has events, determination, snapshot, review task / caseworker action where not eligible, outbox entry, coverage period where approved (T018) |
| TC-83 | FR-003-22, ADR-003-06 | integration | data-lane / benefit-be | test_FR_003_22_collection_counts_match_manifest_after_reset | counts per collection vs `manifest.json` |
| TC-84 | FR-003-22 | integration | data-lane / benefit-be | test_FR_003_22_history_files_reference_existing_determinations_and_cases | `history/*.json` keys resolve to seeded `determination_id` / `case_id` |
| TC-85 | FR-003-12, US4-AS2 | integration | data-lane / benefit-be | test_FR_003_12_every_seeded_record_in_every_collection_is_marked_synthetic | every document in every seeded collection (T019) |
| TC-86 | FR-003-16, ADR-003-03 | integration | workflows-lane / benefit-be | test_FR_003_16_seeded_verified_facts_returns_only_the_scoped_households_members | two seeded households; port called with H1's `Scope.for_worker` (T020) |
| TC-87 | FR-003-19, TW-11 | integration | workflows-lane / benefit-be | test_FR_003_19_snapshot_insert_twice_keeps_one_document | same snapshot inserted twice (T021) |
| TC-88 | FR-003-04, TW-11 | integration | workflows-lane / benefit-be | test_FR_003_04_determination_insert_duplicate_key_is_treated_as_done | same DeterminationRecord inserted twice: no error, one document |
| TC-89 | FR-003-19, ADR-003-03 | unit | workflows-lane / benefit-be | test_FR_003_19_existing_snapshot_for_case_and_date_is_reused | fake store holding a snapshot for `(case, as_of)`; members changed since (T022) |
| TC-90 | FR-003-19, FR-003-21, edge "household size changes" | unit | workflows-lane / benefit-be | test_FR_003_19_snapshot_uses_members_of_the_as_of_year | fake members: 2 in 2025, 3 in 2026; as-of in each year |
| TC-91 | FR-003-16, R8 | unit | workflows-lane / benefit-be | test_FR_003_16_snapshot_from_application_form_maps_attested_facts_and_leaves_identity_unknown | household without seeded members; form with `qualifying_immigrant`, `medicare_entitled=False`, 1 job |
| TC-92 | FR-003-03 | unit | workflows-lane / benefit-be | test_FR_003_03_form_job_without_verified_stub_gives_cannot_determine_not_ineligible | form-only household, declared job, no verified facts |
| TC-93 | FR-003-17 | unit | workflows-lane / benefit-be | test_FR_003_17_verified_facts_merged_into_member_jobs_and_identity | fake VerifiedFacts for 2 members, one job each |
| TC-94 | FR-003-19, VIII | unit | workflows-lane / benefit-be | test_FR_003_19_captured_snapshot_contains_no_member_names | seeded members with synthetic names; JSON of captured snapshot |
| TC-95 | FR-003-04, ADR-003-02 | unit | workflows-lane / benefit-be | test_FR_003_04_same_request_twice_stores_one_record_and_returns_identical_summary | fake stores; activity run twice with one DeterminationRequest (T023, T024) |
| TC-96 | FR-003-19, ADR-003-03 | unit | workflows-lane / benefit-be | test_FR_003_19_member_change_after_capture_does_not_change_determination | determine, change a member's income, determine again for the same case and date |
| TC-97 | FR-003-02, R5 | unit | workflows-lane / benefit-be | test_FR_003_02_summary_maps_each_outcome_to_reason_failed_rules_and_missing_items | parametrized: eligible, ELIG-06 fail, ELIG-01 fail, ELIG-01+06 fail (→ income_over_limit), cannot determine (reason None) |
| TC-98 | FR-003-02, ADR-003-02 | unit | workflows-lane / benefit-be | test_FR_003_02_determination_id_matches_stub_formula | `_id = uuid5(case_id, "determination:<as_of>")` (R6) |
| TC-99 | FR-003-02, TW-10 | workflow | workflows-lane / benefit-be | test_FR_003_02_real_determination_store_failing_past_retries_opens_review_and_does_not_stall | time-skipping env; real activity with a determinations store that always raises; case ends `under_review`, not left `determining` |
| TC-100 | FR-001-03, ADR-003-02 | workflow | workflows-lane / benefit-be | test_FR_001_03_case_replay | main's recorded case histories replay unchanged with the new activity body (TW-14) |
| TC-101 | FR-010-01, ADR-003-02 | workflow | workflows-lane / benefit-be | test_FR_010_01_review_history_replays_without_nondeterminism | main's review history |
| TC-102 | FR-003-16, ADR-003-03 | integration | platform-ui-lane / benefit-be | test_FR_003_16_worker_scope_cannot_read_another_households_seeded_verifications | `Scope.for_worker(case of H1)` querying H2's rows returns none (T025) |
| TC-103 | FR-003-23, US5-AS1 | unit | platform-ui-lane / benefit-be | test_FR_003_23_caseworker_gets_determinations_newest_first_with_reason_code | fake repo: decided case with 2 determinations (ineligible income, then eligible) (T026, T027) |
| TC-104 | FR-003-23, PL-7 | unit | platform-ui-lane / benefit-be | test_FR_003_23_supervisor_can_read_case_determinations | supervisor session |
| TC-105 | FR-003-23, PL-7 | unit | platform-ui-lane / benefit-be | test_FR_003_23_applicant_gets_403_error_envelope | applicant session of the case's own household |
| TC-106 | FR-003-23, constitution IV | unit | platform-ui-lane / benefit-be | test_FR_003_23_applicant_refusal_is_audited | applicant session; fake AuditWriter records the refusal |
| TC-107 | FR-003-23 | unit | platform-ui-lane / benefit-be | test_FR_003_23_unauthenticated_gets_401_error_envelope | no session cookie |
| TC-108 | FR-003-23 | unit | platform-ui-lane / benefit-be | test_FR_003_23_unknown_case_gets_404_error_envelope | caseworker; random UUID with no case |
| TC-109 | FR-003-23 | unit | platform-ui-lane / benefit-be | test_FR_003_23_non_uuid_case_id_gets_422_error_envelope | caseworker; `case_id = "abc"` |
| TC-110 | FR-003-23 | unit | platform-ui-lane / benefit-be | test_FR_003_23_case_without_determination_returns_empty_list | caseworker; case still `verifying` |
| TC-111 | FR-003-23, US5-AS2 | unit | platform-ui-lane / benefit-be | test_FR_003_23_cannot_determine_view_lists_missing_items_and_null_reason | stored Cannot determine record (C's shape: missing `pay_stub`) |
| TC-112 | FR-003-05, VIII | unit | platform-ui-lane / benefit-be | test_FR_003_05_api_rule_inputs_carry_member_ids_never_names | stored record built from named synthetic members; response has no name strings |
| TC-113 | FR-003-23, R11 | unit | platform-ui-lane / benefit-be | test_FR_003_23_determination_read_writes_audit_entry | caseworker read; fake AuditWriter |
| TC-114 | FR-003-23, ADR-003-05 | integration | platform-ui-lane / benefit-be | test_FR_003_23_repository_reads_case_determinations_by_recorded_at_desc_max_20 | 21 records for one case + 1 for another case in MongoDB |
| TC-115 | FR-003-23, FE-3 | contract | platform-ui-lane / benefit-be | test_FR_003_23_committed_openapi_has_list_case_determinations_matching_contract | `openapi/openapi.json` vs `contracts/rest-api.openapi.yaml` (T028) |
| TC-116 | FR-003-23 | unit | platform-ui-lane / benefit-fe | FR-003-23: fetches determinations under key cases/id/determinations when a case id is given | `vi.mock` of the generated client (T029) |
| TC-117 | FR-003-23, FE-3 | contract | platform-ui-lane / benefit-fe | FR-003-23: generated schema types listCaseDeterminations as DeterminationList | regenerated `schema.d.ts` |
| TC-118 | FR-003-23, US5-AS1 | unit | platform-ui-lane / benefit-fe | FR-003-23: shows result, reason code, as-of date and rule set version when the case is determined | mocked ineligible DeterminationView (T030) |
| TC-119 | FR-003-23, FR-003-05 | unit | platform-ui-lane / benefit-fe | FR-003-23: lists each rule's ID, inputs, threshold and outcome when the determination has six rules | mocked eligible view |
| TC-120 | FR-003-23, US5-AS2 | unit | platform-ui-lane / benefit-fe | FR-003-23: lists the missing items when the result is cannot determine | mocked cannot-determine view, reason null |
| TC-121 | FR-003-23 | unit | platform-ui-lane / benefit-fe | FR-003-23: shows an empty state when the case has no determination | mocked `items: []` |
| TC-122 | FR-003-23 | unit | platform-ui-lane / benefit-fe | FR-003-23: shows the error state when the determinations request fails | mocked 404 / 500 ErrorEnvelope |
| TC-123 | FR-003-23 | unit | platform-ui-lane / benefit-fe | FR-003-23: case page renders the determination section when it is registered | `caseSections` (R12) |
| TC-124 | FR-003-23, US5-AS1, quickstart 8 | e2e | platform-ui-lane / benefit-fe | FR-003-23: caseworker sees demo household A's eligible determination with six passing rules matching the API | after `make seed-reset`: applicant A submits `validForm`; caseworker opens the case; each rule row equals `GET …/determinations` (T031) |
| TC-125 | FR-003-23, US5-AS1, quickstart 8 | e2e | platform-ui-lane / benefit-fe | FR-003-23: caseworker sees demo household B ineligible with reason income over limit and ELIG-06 failed | applicant B submits; case under review |
| TC-126 | FR-003-23, US5-AS2, quickstart 8 | e2e | platform-ui-lane / benefit-fe | FR-003-23: caseworker sees the missing pay stub when demo household C cannot be determined | applicant C submits; case under review |
| TC-127 | FR-003-23, FE-12 | e2e | platform-ui-lane / benefit-fe | FR-003-23: determination section has no axe violations | B's case page, section expanded |
| TC-128 | FR-003-23, US5-AS1 | e2e | platform-ui-lane / benefit-fe | FR-003-23: caseworker sees a seeded 2025 history determination with the 2025 rule set version | H-ineligible-2025 from `history/` |
| TC-129 | FR-003-14, FR-003-02, ADR-003-03 | integration | qa / benefit-be | test_FR_003_14_seeded_households_a_b_c_submit_form_and_end_eligible_ineligible_cannot_determine | local MongoDB + Temporal; A/B/C submit `validForm` (T032, quickstart 6) |
| TC-130 | FR-003-23, FR-003-19 | integration | qa / benefit-be | test_FR_003_23_determination_stored_by_workflow_is_readable_through_api | B's case after the workflow; API view equals stored record and snapshot |
| TC-131 | FR-003-05, SC-003-02, FR-003-13, FR-003-22 | integration | qa / benefit-be | test_FR_003_05_every_seeded_history_and_test_set_determination_has_six_rule_trace | every determination in `determinations` and generated test sets after reset (T033) |

## Quality gates
- Coverage: every FR has ≥1 case (`wf.py tasks-gate`), and every case has a test defined with its exact name and not skipped (`wf.py job <feature_dir> trace:strict`).
- Known answers: 100% pass, run twice (SC-003-01, quickstart 1). Property tests run with hypothesis' derandomized CI profile.
- Seed: `manifest.json` hashes identical across two runs (SC-003-03, TC-81).
- Migrations 0001…0005 up and down (TC-72, existing `tests/db/test_migrations.py`).
- API: every error response uses the ErrorEnvelope (main `test_FR_000_18_every_error_response_uses_the_error_envelope`), the route is session-protected (main `test_FR_000_06_every_non_health_route_requires_session`), OpenAPI drift check green in both repos.
- E2E TC-124…128 green with axe (FE-12); main's e2e suite unchanged (ADR-003-03).
- Evals: none — no AI in this feature (constitution I); the engine is deterministic and covered by known answers.
- Not tested, and why:
  - FR-003-22 "pre-written explanations meet the same checks as generated ones (FR-004-11)": not testable yet, because 004 hasn't defined FR-004-11's checks (ADR-003-06 defers the schema test until then). TC-84 checks only that the files reference real records.
  - FR-003-10's "two laptops" (US4-AS1) is proven as two runs on one machine (TC-47, TC-81); CI on macOS and Linux runners covers the cross-machine part.
