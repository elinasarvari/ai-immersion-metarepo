# Tasks: Eligibility Rules and Synthetic Data

**Input**: `specs/003-eligibility-rules/` (spec, plan, research, data-model, contracts/, ADR-003-01…06). All paths are inside `repos/benefit-be` or `repos/benefit-fe`.
**Format**: `- [ ] Txxx [P?] [Lane] [repo] [USn?] description (FRs)`. `[P]` = parallel (other files, no open dependency). Lanes: `[contracts]` shared changes first and alone; `[data]`, `[workflows]`, `[platform-ui]` touch only their folders; `[qa]` runs after the lanes.
**Not tasks**: running checks, starting the stack, e2e runs and walking quickstart.md are done by the verify loop's jobs (check, build, e2e).
**Already on the branch (research R0)**: engine, models, known answers, households and documents generators, migration 0002 (to be renumbered). They are marked [X] where the code satisfies the task. `origin/main` is merged by the integrator first (ADR-003-04).

## Phase 1: Contracts (first, alone)

- [X] T001 [contracts] [benefit-be] Reconcile `packages/domain/eligibility.py` with main: remove `EligibilityResult`, use `case.DeterminationOutcome`; add `DeterminationView` (`determination_id`, `result`, `reason_code: DenialReason|None`, `as_of_date`, `rule_set_id`, `rule_set_version`, `household_size`, `household_monthly_income`, `monthly_income_limit`, `rules: list[RuleResult]`, `missing_items`, `recorded_at`); `DeterminationRecord._id` keeps the stub's `determination_id` formula, `extra="forbid"` (FR-003-02, -05, -23; ADR-003-02, -04)
- [X] T002 [contracts] [benefit-be] Reconcile `packages/domain/household.py`: import `Relationship` and `PayFrequency` from `case.py` (relationship enum = main's 8 values); add `HouseholdSnapshot.as_of_date`; add `VerifiedMemberFacts {household_id, member_id, identity_verified: bool|None, jobs: list[JobIncome]}`; refresh `tests/contract/snapshots/eligibility_models.json` (FR-003-16, -17, -19; ADR-003-03, -04)
- [X] T003 [contracts] [benefit-be] Add path `GET /api/v1/cases/{case_id}/determinations` (`listCaseDeterminations`) and schema `DeterminationView` to the OpenAPI source per `specs/003-eligibility-rules/contracts/rest-api.openapi.yaml` (FR-003-23; ADR-003-05)

## Phase 2: Engine (US1, US2, US3) — [data]

- [X] T004 [data] [benefit-be] [US1] Pure `evaluate(snapshot, as_of_date)` with ELIG-01…06, income counting and outcome precedence in `packages/rules/{engine,checks,income}.py` (FR-003-01, -02, -03, -04, -08, -17, -18, -20)
- [X] T005 [data] [benefit-be] [US2] Per-rule trace: rule ID, inputs, threshold, outcome, policy ref, missing items (FR-003-05)
- [X] T006 [data] [benefit-be] [US3] Effective-dated 2025/2026 rule sets and poverty guidelines in `packages/rules/rule_sets.py`; no rule set for date → Cannot determine "no rules for date" (FR-003-06, -07, -15, -21)
- [X] T007 [data] [benefit-be] [US1] Known-answer cases in `db/seeds/data/known_answers.json` (≥30, every rule, edge case, both years) and `tests/packages/rules/test_known_answers.py` (FR-003-09; SC-003-01)
- [X] T008 [P] [data] [benefit-be] [US1] Property tests (hypothesis) for determinism, limit inclusivity, missing-vs-fail precedence and unchanged inputs in `tests/packages/rules/test_properties.py` (FR-003-04, -20, -08)
- [X] T009 [P] [data] [benefit-be] [US3] Test that seeded `rule_sets` documents equal `RULE_SETS`, and that the same household evaluated as of 2025 and 2026 uses each year's limits, in `tests/packages/rules/test_rule_sets.py` (FR-003-06, -07; ADR-003-01)
- [X] T010 [P] [data] [benefit-be] [US1] `packages/rules/stub.py` imports `POLICY_REFS` instead of its duplicate `_POLICY_REFS` (ADR-003-01)

## Phase 3: Data store and synthetic data (US4) — [data]

- [X] T011 [data] [benefit-be] [US4] Renumber migration to `db/migrations/versions/0005_eligibility.py` (after main's 0002–0004): `households` validator = main's 0003 fields + `address_state`, `seed_key`, minus `stub_result`; strict validators for `household_members`, `household_snapshots` (unique `(case_id, as_of_date)`), `determinations` (index `(case_id, recorded_at desc)`), `rule_sets` (unique `(rule_set_id, version)`); new household-only `seeded_verifications` (unique `(household_id, member_id)`); drop `household_stub_results`; `_meta.anchor_date`; downgrade recreates; update `tests/db/migrations/` (FR-003-06, -19; ADR-003-03, -04)
- [X] T012 [data] [benefit-be] [US4] Merge the generator with main's `db/seeds/generate.py` and `users.py`: link 000's demo users to households A/B/C (FR-003-14); drop `STUB_RESULTS`
- [X] T013 [P] [data] [benefit-be] [US4] 200 households × 2 years, sizes 1–6, 60% under limit, 15% mismatches, multiple jobs, zero income, household changes, missing documents (`db/seeds/households.py`) (FR-003-10, -11)
- [X] T014 [P] [data] [benefit-be] [US4] Pay stub documents, weekly/bi-weekly/monthly, 10% poor quality, visible "SYNTHETIC" marker (`db/seeds/documents.py`) (FR-003-12)
- [X] T015 [data] [benefit-be] [US4] Demo households A/B/C seeded so the real engine gives Eligible / Ineligible (income over limit) / Cannot determine (declared job, no usable stub), with no open case and no current coverage (`db/seeds/households.py`) (FR-003-14; ADR-003-03, -06)
- [X] T016 [data] [benefit-be] [US4] `db/seeds/verifications.py`: seeded identity and verified pay stub facts per member/job into `seeded_verifications` for every seeded household (FR-003-16, -17; ADR-003-03)
- [X] T017 [P] [data] [benefit-be] [US4] `db/seeds/test_sets.py`: `pay_stub_extractions.json` (10–20, 002), `redeterminations_due.json` (007), `expected_metrics.json` (008), `manifest.json` (seed, generator version, file hashes) under `db/seeds/generated/` (FR-003-13; SC-003-03, -04)
- [X] T018 [data] [benefit-be] [US4] `db/seeds/history.py`: decided 2025 and current-period cases for non-demo households with events, determinations, snapshots, coverage periods, review tasks, caseworker actions and approval/denial outbox entries in main's shapes; pre-written explanations and other notice types as `db/seeds/generated/history/*.json` keyed by `determination_id`/`case_id` (FR-003-22; ADR-003-06)
- [X] T019 [data] [benefit-be] [US4] Tests: same seed twice gives identical records and files (SC-003-03); every record and document marked synthetic; collection counts match the manifest; validators accept every document; demo households have no open case or coverage, in `tests/db/seeds/` and `tests/integration/test_seeded_dataset.py` (FR-003-10…14, -22)

## Phase 4: Determination in the workflow (US1, US2) — [workflows]

- [X] T020 [P] [workflows] [benefit-be] [US1] `apps/worker/repositories/verified_facts.py`: `VerifiedFacts` port plus interim implementation reading `seeded_verifications` by `household_id` under `Scope.for_worker`; fake for tests (FR-003-16, -17; ADR-003-03)
- [X] T021 [P] [workflows] [benefit-be] [US1] `apps/worker/repositories/snapshots.py` and `determinations.py`: read/insert via `packages.platform.scope` under `Scope.for_worker`, idempotent on duplicate key (FR-003-19; ADR-003-02, -03)
- [X] T022 [workflows] [benefit-be] [US1] `apps/worker/activities/snapshot.py`: reuse an existing snapshot for `(case_id, as_of_date)`; else build from `household_members` for the as-of year; else from the case's application form (unverified); merge `VerifiedFacts`; no names (FR-003-16, -17, -19, -03; ADR-003-03)
- [X] T023 [workflows] [benefit-be] [US1] Replace the body of `apps/worker/activities/determination.py`: capture snapshot, call `evaluate`, insert `DeterminationRecord` (`_id = determination_id`), return 001's `case.Determination` summary mapped per research R5; signature unchanged; delete `repositories/stub_results.py` and `FixedStubResults`; update `main.py` wiring (FR-003-02, -04, -19; ADR-003-02, -03)
- [X] T024 [P] [workflows] [benefit-be] [US1] Tests in `tests/apps/worker/`: same request twice → one stored record and identical summary; later member change does not alter a determination; mapping per outcome; seeded A/B/C → Eligible / Ineligible / Cannot determine; replay histories unchanged (FR-003-02, -04, -19)

## Phase 5: API and case page (US5) — [platform-ui]

- [X] T025 [platform-ui] [benefit-be] [US5] `packages/platform/scope.py`: add `seeded_verifications` to `SCOPED_HOUSEHOLD_ONLY`, remove `household_stub_results` (separate commit); scope test that the worker cannot read another household's verifications (ADR-003-03)
- [X] T026 [platform-ui] [benefit-be] [US5] `GET /api/v1/cases/{case_id}/determinations` in `apps/api/routers/cases.py` with `services/determinations.py`, `repositories/determinations.py`, `schemas/determinations.py`; caseworker/supervisor guard; newest first; maps to `DeterminationView` with `reason_code` (FR-003-23; ADR-003-05)
- [X] T027 [P] [platform-ui] [benefit-be] [US5] API tests in `tests/apps/api/`: role guard, unknown case, ordering, Cannot determine lists missing items, traces carry member IDs only (FR-003-23, -05)
- [X] T028 [platform-ui] [benefit-be] [US5] Regenerate `openapi/openapi.json` (FR-003-23)
- [X] T029 [platform-ui] [benefit-fe] [US5] Regenerate `openapi/openapi.json` and `src/api/generated/schema.d.ts`; add `src/api/determinations.ts` (TanStack Query hook) with test (FR-003-23)
- [X] T030 [platform-ui] [benefit-fe] [US5] `src/features/caseworker/case-page/DeterminationSection.tsx` with test: result, reason code, as-of date, rule set version; per rule ID, inputs, threshold, outcome; missing items for Cannot determine; accessible; register in `sections.tsx` (FR-003-23, -05)
- [X] T031 [platform-ui] [benefit-fe] [US5] `e2e/caseworker-sees-determination.spec.ts` with axe: seeded Eligible, Ineligible, Cannot determine cases compared with stored determinations; update e2e comments that mention stub results (FR-003-23; ADR-003-03, -05)

## Phase 6: Cross-lane QA — [qa]

- [X] T032 [qa] [benefit-be] Regenerate and commit `openapi/openapi.json` after all API changes, then add an integration test (local MongoDB + Temporal): seeded A/B/C submit the standard form and end Eligible / Ineligible / Cannot determine, with the stored determination readable through the API (FR-003-02, -14, -19, -23; SC-003-02)
- [X] T033 [qa] [benefit-be] Cross-lane test that every determination in the seeded history and test sets carries a complete trace for all six rules (SC-003-02, SC-003-04; FR-003-05, -13, -22)

## Phase 7: Test-first and QA tasks (quality engineer, from test-plan.md)

Each lane's test-first task is written, and failing, before its implementation task. Test names are exactly as in test-plan.md. Existing test tasks map to cases: T008 → TC-61–TC-64; T009 → TC-65, TC-66; T019 → TC-81, TC-83, TC-85; T024 → TC-95–TC-98, TC-100, TC-101; T027 → TC-104–TC-112; T031 → TC-124–TC-128; T032 → TC-129, TC-130; T033 → TC-131.

- [X] T034 [contracts] [benefit-be] Test-first for T001–T002 in `tests/packages/domain/test_eligibility.py` and `test_household.py`: TC-68 (no `EligibilityResult`, main's enums reused), TC-69 (`DeterminationView` fields vs contract, `extra="forbid"`), TC-70 (`VerifiedMemberFacts`), TC-71 (`HouseholdSnapshot.as_of_date` required); TC-06 and TC-16 stay green (FR-003-02, -17, -19, -23; ADR-003-04)
- [X] T035 [P] [data] [benefit-be] [US1] Test-first for T010 in `tests/packages/rules/test_stub.py`: TC-67, the stub's policy refs are `POLICY_REFS` (FR-003-05; ADR-003-01)
- [X] T036 [data] [benefit-be] [US4] Test-first for T011 in `tests/db/migrations/test_0005_eligibility.py` (replaces `test_0002_eligibility.py`): TC-72, TC-73, TC-74 (FR-003-06, -16, -19; ADR-003-03, -04)
- [X] T037 [data] [benefit-be] [US4] Test-first for T012, T015 and T016 in `tests/db/seeds/` and `tests/integration/test_seeded_dataset.py`: TC-56, TC-75 (A/B/C through `evaluate`), TC-76 (no open case or coverage), TC-77 (one verification per seeded member) (FR-003-14, -16, -17; ADR-003-03, -06)
- [X] T038 [data] [benefit-be] [US4] Test-first for T017 and T018 in `tests/db/seeds/test_test_sets.py` and `test_history.py`: TC-78, TC-79, TC-80, TC-82, TC-84 (FR-003-13, -22; ADR-003-06)
- [X] T039 [P] [data] [benefit-be] [US4] `db/seeds/generated/history/README.md`: what the pre-written explanation and notice files hold and how they are keyed, as the follow-up note to 004 and 011 (ADR-003-06 "Work this creates"; FR-003-22)
- [X] T040 [workflows] [benefit-be] [US1] Test-first for T020 and T021 in `tests/integration/worker/`: TC-86 (verified facts scoped to the household), TC-87 (snapshot insert idempotent), TC-88 (duplicate determination counts as done) (FR-003-04, -16, -19; TW-11)
- [X] T041 [workflows] [benefit-be] [US1] Test-first for T022 in `tests/apps/worker/activities/test_snapshot.py`, with fakes: TC-89, TC-90 (members of the as-of year), TC-91 (form mapping, R8), TC-92, TC-93, TC-94 (FR-003-03, -16, -17, -19, -21; ADR-003-03)
- [X] T042 [workflows] [benefit-be] [US1] Test-first for T023 in `tests/apps/worker/activities/test_determination.py` and `tests/apps/worker/workflows/test_determination_failures.py`: TC-95–TC-98, and TC-99 (the real activity's store fails past its retries → the case goes under review and is not left in `determining`; TW-10) (FR-003-02, -04, -19; ADR-003-02)
- [X] T043 [platform-ui] [benefit-be] [US5] Test-first for T025 in `tests/db/test_scope.py`: TC-102, the worker cannot read another household's `seeded_verifications` (FR-003-16; ADR-003-03)
- [X] T044 [platform-ui] [benefit-be] [US5] Test-first for T026 in `tests/apps/api/test_determinations.py` and `tests/integration/api/test_determinations_repository.py`: TC-103, TC-113 (read audited), TC-105–TC-109 (403 with the refusal audited, 401, 404, 422, each asserting the ErrorEnvelope), TC-110, TC-114 (FR-003-23; ADR-003-05; PL-7)
- [X] T045 [platform-ui] [benefit-fe] [US5] Test-first for T029: TC-116 in `src/api/determinations.test.ts`, TC-117 in `src/api/generated.test.ts` (FR-003-23; FE-3)
- [X] T046 [platform-ui] [benefit-fe] [US5] Test-first for T030 in `DeterminationSection.test.tsx` and `sections.test.tsx`: TC-118–TC-123, including the empty and error states (FR-003-05, -23)
- [X] T047 [platform-ui] [benefit-fe] [US5] Page object `e2e/pages/DeterminationSection.ts` for T031's spec (no raw selectors in specs); TC-128 opens a seeded 2025 history case (FR-003-23; ADR-003-05)
- [X] T048 [qa] [benefit-be] Contract test TC-115 in `tests/contract/test_openapi_determinations.py`: the committed `openapi/openapi.json` (after T032 regenerates it) has `listCaseDeterminations` and `DeterminationView` exactly as `specs/003-eligibility-rules/contracts/rest-api.openapi.yaml` (FR-003-23; ADR-003-05)

## Dependencies

- T001–T003 first and alone; every other task depends on them. Integrator merges `origin/main` before T001.
- Data (T008–T019), workflows (T020–T024) and platform-ui (T025–T031) run in parallel once contracts are done. T011 before T016, T018. T020–T022 before T023. T026 before T028, T029–T031. T025 and T011 touch the same collection names and need to agree.
- Test-first: T034 before T001–T002; T035 before T010; T036 before T011; T037 before T012, T015, T016; T038 before T017, T018; T040 before T020, T021; T041 before T022; T042 before T023; T043 before T025; T044 before T026; T045 before T029; T046 before T030; T047 with T031.
- [qa] T032–T033 and T048 last (T048 after T032). benefit-be PR opens before benefit-fe.

## FR coverage

FR-003-01…09: T004–T010 · FR-003-10…13: T013, T014, T017, T019 · FR-003-14: T012, T015, T031 · FR-003-15: T006 · FR-003-16, -17: T002, T016, T020, T022 · FR-003-18, -20, -21: T004, T006, T008 · FR-003-19: T002, T011, T021–T024 · FR-003-22: T018, T019, T033 · FR-003-23: T001, T003, T026–T032
