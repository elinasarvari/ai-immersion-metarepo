# Test plan: 001-case-lifecycle

**Inputs:** spec.md, plan.md, data-model.md, contracts/ (case-workflow.md, rest-api.openapi.yaml), research.md (R1, R3, R7, R9, R10), Accepted ADRs ADR-001-01 … ADR-001-06, tasks.md T001–T030.
**Target repo:** `repos/benefit-be` only (no `benefit-fe` change; UI is 006).
**Rules that set the levels:** testing.md (names, AAA, fixed clock), TW-13 (time-skipping per signal), TW-14 (replay), TW-15 (stubbed activities), TW-16 (restart), KD-3 (property + edge examples for pure rules), KD-11 (migration downgrade), PL-7 (role rejection per route), PL-11 (no reason text in logs), PR-3 / BA-11 (synthetic seed data only), FR-000-20 (no live model in CI), FR-000-27 (dates and time zones).

Proves column: requirement first (the test name starts with it), then acceptance scenario / edge case / success criterion, then the rule that requires the level.

## Cases

| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-001-01, FR-001-23; testing.md | unit | contracts / benefit-be | test_FR_001_01_case_id_for_same_reference_is_stable | literal refs `sub-A`, `sub-B` |
| TC-02 | FR-001-11, US3-AS1; testing.md | unit | contracts / benefit-be | test_FR_001_11_case_status_at_risk_at_ten_days_or_fewer | parametrize days_remaining 11, 10, 9, 0, null |
| TC-03 | FR-001-20; testing.md | unit | contracts / benefit-be | test_FR_001_20_override_request_requires_reason_up_to_500_chars | reason None, "", 500 chars, 501 chars |
| TC-04 | FR-001-13; ADR-001-03 | unit | platform-ui-lane / benefit-be | test_FR_001_13_case_now_follows_scale_and_offset | clock scale 1 and 1440, offset 0 and 86400 |
| TC-05 | FR-001-18, FR-000-27; ADR-001-03 | unit | platform-ui-lane / benefit-be | test_FR_001_18_case_today_is_chicago_date_across_dst_and_midnight_utc | real_now 2026-11-01T06:30Z, 2026-03-08T07:30Z, 2026-12-31T05:59Z |
| TC-06 | FR-001-23, FR-001-22; ADR-001-06 | unit | platform-ui-lane / benefit-be | test_FR_001_23_worker_scope_filters_coverage_by_household_and_refuses_households | case C1 / household H1 |
| TC-07 | FR-001-10; ADR-001-06 | unit | platform-ui-lane / benefit-be | test_FR_001_10_worker_scope_filters_case_collections_by_case_id | case C1 / household H1 |
| TC-08 | FR-001-01, US1-AS1; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_01_decision_deadline_is_45_calendar_days_after_receipt | 2026-01-31, 2026-12-20, 2028-02-14 (leap) |
| TC-09 | FR-001-02, US1-AS5; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_02_only_table_transitions_are_allowed | parametrize every (from, to) pair of CaseState |
| TC-10 | FR-001-02; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_02_transitions_reserved_for_010_and_011_are_refused | awaiting_applicant rows |
| TC-11 | FR-001-22, US1-AS2; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_22_coverage_starts_first_of_receipt_month_ends_last_day_of_12th_month | 2026-03-17 → 2026-03-01..2027-02-28; 2026-01-01; 2026-12-31; 2027-03-31 (leap end 2028-02-29) |
| TC-12 | FR-001-22; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_22_coverage_is_always_twelve_whole_months_property | hypothesis dates 2020–2040 |
| TC-13 | FR-001-18; KD-3 | unit | workflows-lane / benefit-be | test_FR_001_18_deadline_minus_receipt_is_always_45_days_property | hypothesis dates 2020–2040 |
| TC-14 | FR-001-07; ADR-001-04 | unit | workflows-lane / benefit-be | test_FR_001_07_allowed_actions_for_001_review_reasons | adverse_determination, cannot_determine, other four reasons → empty |
| TC-15 | FR-001-16; TW-15, R1 | unit | workflows-lane / benefit-be | test_FR_001_16_stub_determination_follows_household_stub_field | seed households stub=eligible / ineligible / cannot_determine |
| TC-16 | FR-001-20, PL-11 | unit | workflows-lane / benefit-be | test_FR_001_20_record_case_change_never_logs_override_reason | override reason "SYNTH-REASON-123", caplog |
| TC-17 | FR-001-13; TW-15 | workflow | workflows-lane / benefit-be | test_FR_001_13_case_now_wf_uses_workflow_now | time-skipping env, clock scale 1440 |
| TC-18 | FR-001-04, SC-001-01; ADR-001-01 | integration | workflows-lane / benefit-be | test_FR_001_04_record_case_change_retry_is_noop | same CaseChange twice, Mongo replica set |
| TC-19 | FR-001-10; ADR-001-01 | integration | workflows-lane / benefit-be | test_FR_001_10_case_change_writes_event_with_times_actor_reason | CaseChange seq 1, actor `system` |
| TC-20 | FR-001-10; ADR-001-01 | integration | workflows-lane / benefit-be | test_FR_001_10_stale_seq_does_not_overwrite_case | seq 3 applied, then seq 2 |
| TC-21 | FR-001-20, edge case override; ADR-001-01 | integration | workflows-lane / benefit-be | test_FR_001_20_override_outcome_stored_and_determination_unchanged | determination D1 ineligible, reviewer `cw-synth-1` |
| TC-22 | FR-001-22 | integration | workflows-lane / benefit-be | test_FR_001_22_coverage_period_written_once_with_deterministic_id | approved CaseChange applied twice |
| TC-23 | FR-001-04; ADR-001-01 | integration | workflows-lane / benefit-be | test_FR_001_04_failed_transaction_writes_nothing | outbox insert forced to fail mid-transaction |
| TC-24 | FR-001-23; ADR-001-02, KD-11 | integration | data-lane / benefit-be | test_FR_001_23_partial_unique_index_allows_one_open_case_per_household | H1 open case + second open insert; closed case + open insert |
| TC-25 | FR-001-01; ADR-001-02 | integration | data-lane / benefit-be | test_FR_001_01_submission_reference_is_unique | two cases with `sub-A` |
| TC-26 | FR-001-04; ADR-001-01 | integration | data-lane / benefit-be | test_FR_001_04_case_events_case_id_seq_is_unique | two events C1 seq 1 |
| TC-27 | FR-001-02; KD-11 | integration | data-lane / benefit-be | test_FR_001_02_validator_rejects_unknown_case_state_and_outcome | state `closed`, outcome `maybe`, free-text reason_code |
| TC-28 | FR-001-01; KD-11 | integration | data-lane / benefit-be | test_FR_001_01_migration_0002_downgrade_restores_baseline_validators | upgrade → downgrade → upgrade |
| TC-29 | FR-001-16; PR-3, BA-11 | integration | data-lane / benefit-be | test_FR_001_16_seed_covers_every_stub_result_with_synthetic_households | `make dev` seed |
| TC-30 | FR-001-16, US1-AS2; TW-13, TW-15 | workflow | workflows-lane / benefit-be | test_FR_001_16_eligible_decides_approved | stub eligible; asserts coverage + `approval` notice in one change |
| TC-31 | FR-001-09, US1-AS3, SC-001-02; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_09_ineligible_waits_for_approve_denial | stub ineligible (income); `approve_denial` signal |
| TC-32 | FR-001-16, US1-AS4, SC-001-03; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_16_cannot_determine_opens_task_never_decides | stub cannot_determine, missing_items [pay_stub] |
| TC-33 | FR-001-20, edge case override; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_20_override_keeps_determination | `override_to_approve` with reason |
| TC-34 | FR-001-02, US1-AS5; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_02_disallowed_action_recorded_rejected | signal on decided case; action not in allowed list |
| TC-35 | FR-001-04; TW-13, R10 | workflow | workflows-lane / benefit-be | test_FR_001_04_duplicate_request_id_ignored | same request_id signalled twice |
| TC-36 | FR-001-13, edge case demo profile; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_13_events_carry_case_and_real_time | clock scale 1440 |
| TC-37 | FR-001-16, edge case income + other rule; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_16_income_and_other_rule_fail_denies_income_over_limit | stub ineligible failed_rules [other_rule, income] |
| TC-38 | FR-001-07; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_07_review_wait_holds_no_pending_activity | describe() while under_review: no pending activities |
| TC-39 | FR-001-09, SC-001-02; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_09_ineligible_stays_under_review_past_deadline_without_action | time skip 60 days, no signal |
| TC-40 | FR-001-20; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_20_override_without_reason_recorded_rejected | `override_to_approve`, reason None |
| TC-41 | FR-001-07; TW-13, ADR-001-04 | workflow | workflows-lane / benefit-be | test_FR_001_07_allowed_actions_query_lists_open_task_actions | under_review, then decided → empty |
| TC-42 | FR-001-02, US1-AS1; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_02_happy_path_visits_submitted_verifying_determining_decided | stub eligible; event sequence |
| TC-43 | FR-001-10; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_10_every_state_change_recorded_with_actor_and_reason | all paths; seq contiguous from 1 |
| TC-44 | FR-001-11, US3-AS1; TW-13, R3 | workflow | workflows-lane / benefit-be | test_FR_001_11_day_36_shows_9_remaining_at_risk | time skip 36 days, under_review |
| TC-45 | FR-001-11; TW-13 | workflow | workflows-lane / benefit-be | test_FR_001_11_decided_case_has_no_days_remaining | decided case |
| TC-46 | FR-001-03, SC-001-05; TW-14, R9 | workflow | workflows-lane / benefit-be | test_FR_001_03_case_replay | histories case_approved.json, case_override.json |
| TC-47 | FR-001-03, US2-AS1, SC-001-01; TW-16 | workflow | workflows-lane / benefit-be | test_FR_001_03_restart_mid_verification | worker stopped inside verify_documents |
| TC-48 | FR-001-03, edge case restart on task, SC-001-01; TW-16 | workflow | workflows-lane / benefit-be | test_FR_001_03_restart_while_waiting_on_task_no_second_task | worker stopped while under_review |
| TC-49 | FR-001-04, US2-AS2, SC-001-01; TW-16 | workflow | workflows-lane / benefit-be | test_FR_001_04_restart_after_approval_requests_no_second_notice | worker stopped after record_case_change(approved) completes, before workflow completes |
| TC-50 | FR-001-01, US1-AS1; testing.md | unit | platform-ui-lane / benefit-be | test_FR_001_01_submit_opens_submitted_case_with_deadline_45_days | fake repo + fake Temporal client, fixed clock 2026-03-17 |
| TC-51 | FR-001-23, US1-AS6; ADR-001-02 | unit | platform-ui-lane / benefit-be | test_FR_001_23_same_submission_twice_returns_existing_case | `sub-A` twice → 201 then 200, one start |
| TC-52 | FR-001-23, US1-AS6; ADR-001-02 | unit | platform-ui-lane / benefit-be | test_FR_001_23_household_with_open_case_refused_with_reason | H1 open case, `sub-B` → household_has_open_case |
| TC-53 | FR-001-23; ADR-001-02 | unit | platform-ui-lane / benefit-be | test_FR_001_23_household_with_unended_coverage_refused | coverage end_date = today → household_has_coverage |
| TC-54 | FR-001-23; KD-3 boundary | unit | platform-ui-lane / benefit-be | test_FR_001_23_coverage_ended_yesterday_allows_new_application | coverage end_date = today − 1 |
| TC-55 | FR-001-01; ADR-001-02 | unit | platform-ui-lane / benefit-be | test_FR_001_01_temporal_down_returns_503_and_retry_starts_workflow | fake Temporal raises, then succeeds |
| TC-56 | FR-001-13; ADR-001-03 | unit | platform-ui-lane / benefit-be | test_FR_001_13_demo_profile_case_clock_scale_1440 | DEMO_PROFILE true / false |
| TC-57 | FR-001-23; PL-7 | unit | platform-ui-lane / benefit-be | test_FR_001_23_household_taken_from_principal_not_body | body carries foreign household_id |
| TC-58 | FR-001-01; PL-7 | unit | platform-ui-lane / benefit-be | test_FR_001_01_submit_application_rejects_non_applicant_roles | caseworker, supervisor → 403; anonymous → 401 |
| TC-59 | FR-001-09; PL-7 | unit | platform-ui-lane / benefit-be | test_FR_001_09_review_action_rejects_applicant_role | applicant → 403; anonymous → 401 |
| TC-60 | FR-001-20; PL-7 | unit | platform-ui-lane / benefit-be | test_FR_001_20_override_without_reason_returns_422 | reason missing / 501 chars |
| TC-61 | FR-001-07, US1-AS5; ADR-001-04 | unit | platform-ui-lane / benefit-be | test_FR_001_07_action_not_allowed_returns_409 | fake allowed_actions query → empty |
| TC-62 | FR-001-07, FR-001-09; ADR-001-04 | unit | platform-ui-lane / benefit-be | test_FR_001_07_allowed_action_signals_with_principal_reviewer_returns_202 | caseworker `cw-synth-1`, body reviewer ignored |
| TC-63 | FR-001-20, PL-11 | unit | platform-ui-lane / benefit-be | test_FR_001_20_review_action_logs_no_reason_text | reason "SYNTH-REASON-123", caplog |
| TC-64 | FR-001-11, US3-AS1; ADR-001-03 | unit | platform-ui-lane / benefit-be | test_FR_001_11_get_case_returns_days_remaining_and_at_risk | stored clock, case 36 days old |
| TC-65 | FR-001-11; PL-7 | unit | platform-ui-lane / benefit-be | test_FR_001_11_get_case_of_other_household_returns_404 | applicant H2 reads H1 case |
| TC-66 | FR-001-01, FR-001-11, FR-001-23; constitution VI | contract | qa / benefit-be | test_FR_001_01_openapi_matches_case_lifecycle_contract | contracts/rest-api.openapi.yaml vs openapi/openapi.json |
| TC-67 | FR-001-07; constitution VI | contract | qa / benefit-be | test_FR_001_07_registered_workflow_names_match_contract | names in contracts/case-workflow.md vs worker registry |
| TC-68 | FR-001-23, US1-AS6; ADR-001-02 | integration | qa / benefit-be | test_FR_001_23_concurrent_same_submission_opens_one_case_one_workflow | 10 parallel POSTs `sub-A` |
| TC-69 | FR-001-23; ADR-001-02 | integration | qa / benefit-be | test_FR_001_23_concurrent_different_submissions_same_household_open_one | `sub-A`, `sub-B` in parallel for H1 |
| TC-70 | FR-001-10; R7 | integration | qa / benefit-be | test_FR_001_10_audit_entry_commits_and_rolls_back_with_case_change | benefit_audit write forced to fail |
| TC-71 | FR-001-01, US1-AS1, US1-AS2, FR-001-22 | integration | qa / benefit-be | test_FR_001_01_journey_submit_to_approved_with_coverage_and_notice | seed household stub=eligible, real Mongo + Temporal dev server |
| TC-72 | FR-001-09, US1-AS3 | integration | qa / benefit-be | test_FR_001_09_journey_ineligible_approve_denial_decides_denied | seed household stub=ineligible |
| TC-73 | FR-001-20, edge case override | integration | qa / benefit-be | test_FR_001_20_journey_override_to_approve_keeps_determination | seed household stub=ineligible |
| TC-74 | FR-001-16, US1-AS4, SC-001-03 | integration | qa / benefit-be | test_FR_001_16_journey_cannot_determine_waits_on_task | seed household stub=cannot_determine |
| TC-75 | FR-001-03, FR-001-04, SC-001-01; TW-16 | integration | qa / benefit-be | test_FR_001_03_journey_worker_restart_no_duplicate_effects | real worker process killed mid-case; count events, tasks, outbox |
| TC-76 | FR-001-11; ADR-001-03 | integration | qa / benefit-be | test_FR_001_11_api_status_matches_workflow_status_query | same case via GET and `status` query |
| TC-77 | FR-001-13, edge case demo profile | integration | qa / benefit-be | test_FR_001_13_demo_profile_history_has_case_and_real_times | DEMO_PROFILE=true |

## Files

- contracts: `tests/packages/domain/test_case.py` (TC-01–03)
- platform-ui: `tests/packages/platform/test_clock.py` (TC-04, 05), `test_scope_filter.py` (TC-06, 07), `tests/apps/api/services/test_cases.py` (TC-50–57), `tests/apps/api/routers/test_applications.py` (TC-58), `tests/apps/api/routers/test_cases.py` (TC-59–65)
- workflows: `tests/apps/worker/workflows/test_case_states.py` (TC-08–14), `tests/apps/worker/activities/test_stubs.py` (TC-15), `test_case_record.py` (TC-16), `tests/apps/worker/workflows/test_calendar.py` (TC-17), `tests/apps/worker/repositories/test_cases.py` (TC-18–23), `tests/apps/worker/workflows/test_case.py` (TC-30–45), `test_case_replay.py` (TC-46), `test_case_restart.py` (TC-47–49)
- data: `tests/db/test_migrations.py` (TC-24–28), `tests/db/seeds/test_reset.py` (TC-29)
- qa: `tests/contract/test_case_lifecycle_contract.py` (TC-66, 67), `tests/integration/test_case_submission.py` (TC-68, 69), `test_case_audit.py` (TC-70), `test_case_journey.py` (TC-71–74, 76, 77), `test_case_restart.py` (TC-75)

## Quality gates

- Coverage: every FR has ≥1 case (`wf.py tasks-gate`), and every case has a test defined with its exact name and not skipped (`wf.py job <feature_dir> trace:strict`).
- Every acceptance scenario (US1-AS1–6, US2-AS1–2, US3-AS1), edge case and SC-001-01/02/03/05 has ≥1 case above.
- `make test-unit test-workflow test-contract` and `make test-integration` green; replay (TC-46) and restart (TC-47–49) run on every PR (SC-001-05).
- No live model, no real agent, no DB in workflow tests (TW-15, FR-000-20); all data synthetic from the seed generator or literal `SYNTH-` values (PR-3, BA-11).
- Evals: none — 001 has no AI output (verification and determination are stubs; 002 and 003 own their evals).
- Not tested, and why: none.

## Findings

- **FR-001-16 precedence has no owner in tasks.md.** "Income and another rule both fail → income over limit" is not assigned to `case_states.py` or the determination stub; T013 copies `denial_reason` from the determination. TC-37 checks the outcome at workflow level; the implementer must place the rule (pure helper in `case_states.py` recommended, so 003 can't change it silently).
- **US1-AS2/AS3 "notice requested"** is provable only as an `outbox` record with `status: requested` until 011 (spec Assumptions); TC-30, TC-71, TC-72 assert that, not delivery.
- **No end-to-end screen journey (FE-12):** no `benefit-fe` change in 001; the API ↔ worker ↔ Mongo journeys run as `[qa]` integration tests (TC-71–77). 006 adds the screen journeys.
- **`wf.py tasks-gate` fails on IDs 001 doesn't own.** `spec_frs()` (`workflows/benefit-feature/scripts/wf.py:142`) takes every `FR-…` mentioned in spec.md, so the "Moved requirements" table and cross-references (FR-001-05/06/08/12/14/15/17/19/21, FR-010-01…04, FR-011-01/02/04…07) count as uncovered. All 14 requirements 001 defines (`**FR-001-xx**`) are covered. Fix: have `spec_frs` read only the bold definitions, as `check_spec` already does (line 153); `trace:strict` has the same problem. Not fixed here: the quality engineer must not edit `workflows/`.
- **R7 is unverified** (cross-database transaction including `benefit_audit`); TC-70 is the check — if it fails, raise an ADR amendment rather than weakening the test.
