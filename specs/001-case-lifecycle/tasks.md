---

description: "Task list for 001 Case lifecycle"
---

# Tasks: Case Lifecycle

**Input**: Design documents from `specs/001-case-lifecycle/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md, decisions/)

**Prerequisites**: plan.md, spec.md, Accepted ADRs ADR-001-01 … ADR-001-06 (ADR-001-04 = Option B signal + `allowed_actions` query; ADR-001-05 = Option A, 001 ships the three endpoints)

**Target repo**: `repos/benefit-be` only. All paths below are relative to `repos/benefit-be/`. No `benefit-fe` change (UI is 006).

**Tests**: Required (constitution V, test-first). Each lane task includes its own unit tests named `test_FR_001_xx_…`; cross-lane integration, replay and restart suites are added by the quality engineer as `[qa]` tasks (test-strategy skill).

**Organization**: Tasks are grouped by user story. Every task carries one lane tag and its repo tag. `[contracts]` = shared changes (`packages/domain/`, OpenAPI, dependencies, lockfiles, Makefile/Procfile); every other task touches only its lane's folders: `[workflows]` → `apps/worker/`, `tests/apps/worker/`; `[data]` → `db/`, `tests/db/`; `[platform-ui]` → `apps/api/`, `packages/platform/`, `tests/apps/api/`, `tests/packages/platform/`.

## Format: `[ID] [P?] [Story?] [lane] [repo] Description (FR IDs)`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3 (spec.md)
- Rule sets per lane: `project-rules/README.md` (workflows → temporal-workflows.md; data → data-knowledge.md, database.md; platform-ui → platform-api.md, api-generation.md; contracts → backend-architecture.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch and baseline. No new dependency (plan: constitution X, PR-4).

- [X] T001 [contracts] [benefit-be] Create branch `feature/001-case-lifecycle` in `repos/benefit-be`, run `make doctor` and `make check` to confirm a green baseline; confirm `pyproject.toml` and `uv.lock` need no change (temporalio 1.35.0, FastAPI 0.162.2, PyMongo 4.19.0 already pinned) (FR-001-03)

---

## Phase 2: Foundational (Blocking Prerequisites — contracts step, then lane foundations)

**Purpose**: Contracts merged before lanes start (constitution VI, BA-8), then the clock, scope and storage every story uses.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Contracts step

- [X] T002 [contracts] [benefit-be] Create `packages/domain/case.py` with the enums from data-model.md, values exactly as listed: `CaseType` (`application`, `redetermination`), `CaseState` (`submitted`, `verifying`, `awaiting_applicant`, `determining`, `under_review`, `decided`), `CaseOutcome` (`approved`, `denied`, reserved `renewed_automatically`, `renewed_after_response`, `ended_by_caseworker`), `DenialReason` (`income_over_limit`, `other_rule_not_met`, `missing_information`), `ReviewReason` (full FR-010-01 list of six), `CaseworkerActionType` (all eleven values), `CaseEventKind` (`state_changed`, `review_task_opened`, `caseworker_action`, `action_rejected`, `notice_requested`, `coverage_started`, `demo_action`), `DeterminationOutcome` (`eligible`, `ineligible`, `cannot_determine`), `SubmissionRefusal` (`household_has_open_case`, `household_has_coverage`), `CoverageStatus` (`active`, `continued_pending_review`, `renewed`, `ended`) (FR-001-02, FR-001-16, FR-001-23)
- [X] T003 [contracts] [benefit-be] Add the Pydantic v2 models to `packages/domain/case.py`: `CaseClock` (`real_start`, `case_start`, `scale: int` "1, or 1440 in the demo profile", `offset_seconds: int = 0`), `CaseStart`, `Case`, `CaseEvent` (`reason_code: str` "enum-backed, no free text", `case_time` + `real_time`), `ReviewTask` (`reminder: bool = false`, `escalated: bool = false`), `CaseworkerActionRequest` (`reason: str | null` "required for `override_to_approve`, max 500 chars, never logged"), `CaseworkerAction` (`_id` = `request_id`; `outcome` `applied` | `rejected`), `CoveragePeriod`, `NoticeRequest` (`notice_type` `approval` | `denial`, `status: requested`), minimal `Determination`, `VerificationRequest`, `VerificationOutcome`, `DeterminationRequest`, `CaseChange`, `CaseStatus` (`days_remaining: int | null` "null once decided", `at_risk` = `days_remaining <= 10`), `AllowedActions`, `ApplicationSubmission`; plus `SUBMISSION_NS` and helpers `case_id_for(submission_reference)` = `uuid5(SUBMISSION_NS, ref)` and `workflow_id_for(case_id)` = `case-{case_id}`; unit tests in `tests/packages/domain/test_case.py` (FR-001-01, FR-001-10, FR-001-13, FR-001-16, FR-001-20, FR-001-22)
- [X] T004 [contracts] [benefit-be] Add the three paths and schemas of `specs/001-case-lifecycle/contracts/rest-api.openapi.yaml` (`submitApplication`, `getCase`, `submitReviewAction`; `ReviewActionBody.action` enum `approve_denial`, `override_to_approve`; `reason` maxLength 500) to `openapi/openapi.json` via `scripts/export_openapi.py` once routers exist (T020, T021, T027); this task fixes the contract text the platform-ui routers must produce, and `make openapi-check` must pass at the end (FR-001-01, FR-001-11, FR-001-23)

### Test-first (quality engineer; write failing, then the task below makes them pass)

- [X] T031 [contracts] [benefit-be] Before T003: write failing TC-01, TC-02, TC-03 in `tests/packages/domain/test_case.py` (test-plan.md) (FR-001-01, FR-001-11, FR-001-20)
- [X] T032 [P] [platform-ui] [benefit-be] Before T005, T006: write failing TC-04, TC-05 in `tests/packages/platform/test_clock.py` and TC-06, TC-07 in `tests/packages/platform/test_scope_filter.py` (FR-001-10, FR-001-13, FR-001-18, FR-001-23)
- [X] T033 [P] [data] [benefit-be] Before T007: write failing TC-24–TC-28 in `tests/db/test_migrations.py` (unique and partial indexes, validators, downgrade; KD-11) (FR-001-01, FR-001-02, FR-001-04, FR-001-23)
- [X] T034 [P] [workflows] [benefit-be] Before T008: write failing TC-17 in `tests/apps/worker/workflows/test_calendar.py` (FR-001-13)

### Lane foundations (parallel after T002–T003)

- [X] T005 [P] [platform-ui] [benefit-be] Add `case_now(clock: CaseClock, real_now: datetime) -> datetime` (= `case_start + (real_now - real_start) * scale + offset_seconds`) and `case_today(clock, real_now) -> date` (Chicago calendar date) to `packages/platform/clock.py`, pure, no settings read; tests with scale 1 and 1440 and a DST boundary in `tests/packages/platform/test_clock.py` (ADR-001-03; FR-001-13, FR-001-18)
- [X] T006 [P] [platform-ui] [benefit-be] Add `ScopeKind.worker` and `Scope.for_worker(case_id, household_id)` to `packages/platform/scope.py`: filter `case_id` on case collections, `household_id` on `SCOPED_HOUSEHOLD_ONLY` (`coverage_periods`), refuse `households` and `users`; tests in `tests/packages/platform/test_scope_filter.py` (ADR-001-06; FR-001-10, FR-001-22, FR-001-23)
- [X] T007 [P] [data] [benefit-be] Create migration `db/migrations/versions/0002_case_lifecycle.py` tightening the `0001_baseline` validators for `cases`, `case_events`, `review_tasks`, `caseworker_actions`, `coverage_periods`, `outbox` to the data-model.md fields and enums; indexes: unique `cases.submission_reference`, partial unique `cases.household_id` where `open: true`, `cases(state, decision_deadline)`, unique `case_events(case_id, seq)`, `review_tasks(status, opened_real_time)`, `coverage_periods(household_id, end_date)`; with downgrade (KD-11); tests in `tests/db/test_migrations.py` (ADR-001-01, ADR-001-02; FR-001-01, FR-001-04, FR-001-23)
- [X] T008 [P] [workflows] [benefit-be] Add the case-clock wrapper to `apps/worker/workflows/calendar.py` (`case_now_wf(clock)` / `case_today_wf(clock)` calling `packages/platform/clock` with `workflow.now()` through `imports_passed_through`); tests in `tests/apps/worker/workflows/test_calendar.py` (depends on T005) (ADR-001-03; FR-001-13, FR-001-18)

**Checkpoint**: contracts merged, clock, scope and migration in place — lanes can start in parallel.

---

## Phase 3: User Story 1 - Application moves from submission to decision (Priority: P1) 🎯 MVP

**Goal**: A submission opens exactly one case, which moves submitted → verifying → determining → decided (approved) or → under_review → decided (denied / override-approved) through the review gate, with history, coverage and notice requests.

**Independent Test**: With stubbed verification and determination, submit applications and confirm each reaches the expected outcome through the expected stages; resolve review tasks with `approve_denial` or `override_to_approve` (quickstart steps 1–5).

### Workflows lane

- [X] T035 [P] [US1] [workflows] [benefit-be] Before T009, T010, T012: write failing TC-08–TC-14 (incl. hypothesis TC-12, TC-13; KD-3) in `tests/apps/worker/workflows/test_case_states.py`, TC-15 in `tests/apps/worker/activities/test_stubs.py`, TC-16 in `tests/apps/worker/activities/test_case_record.py` (FR-001-01, FR-001-02, FR-001-07, FR-001-16, FR-001-18, FR-001-20, FR-001-22)
- [X] T036 [P] [US1] [workflows] [benefit-be] Before T011: write failing integration TC-19–TC-23 in `tests/apps/worker/repositories/test_cases.py` against the replica-set MongoDB (FR-001-04, FR-001-10, FR-001-20, FR-001-22)
- [X] T037 [US1] [workflows] [benefit-be] Before T013, T014: write failing time-skipping tests TC-30–TC-43 in `tests/apps/worker/workflows/test_case.py` with stubbed activities (TW-13, TW-15); T016 owns TC-30–TC-36 and is done when all of TC-30–TC-43 pass; TC-37 needs the FR-001-16 precedence placed (test-plan.md Findings) (FR-001-02, FR-001-04, FR-001-07, FR-001-09, FR-001-10, FR-001-13, FR-001-16, FR-001-20)
- [X] T009 [P] [US1] [workflows] [benefit-be] Create pure `apps/worker/workflows/case_states.py`: transition table from data-model.md (001 rows active; 010/011 rows listed but refused until those features), `can_transition(from, to)`, `allowed_actions_for(reason)` (001: `adverse_determination`/`cannot_determine` → `approve_denial`, `override_to_approve`), `decision_deadline(received_on)` = `received_on + 45` calendar days, `coverage_for(received_on)` → (first day of receipt month, last day of the 12th month; e.g. 2026-03-17 → 2026-03-01 to 2027-02-28); tests `test_FR_001_02_*`, `test_FR_001_01_*`, `test_FR_001_22_*` in `tests/apps/worker/workflows/test_case_states.py` (FR-001-01, FR-001-02, FR-001-18, FR-001-22)
- [X] T010 [P] [US1] [workflows] [benefit-be] Create stub activities `apps/worker/activities/verification.py` (`verify_documents`: `VerificationRequest` → `VerificationOutcome`) and `apps/worker/activities/determination.py` (`determine_eligibility`: `DeterminationRequest` → minimal `Determination`), names per `contracts/case-workflow.md`, result chosen by a test fixture or by the seeded household's stub field (research R1), pure and idempotent; tests in `tests/apps/worker/activities/test_stubs.py` (FR-001-16)
- [X] T011 [P] [US1] [workflows] [benefit-be] Create `apps/worker/repositories/cases.py`: all writes of a `CaseChange` in one transaction via `packages/platform/mongo.py` with `Scope.for_worker` — `case_events` insert keyed by unique `(case_id, seq)`, `cases` update guarded by `last_seq < seq`, `review_tasks` open/resolve, `caseworker_actions` (`_id` = `request_id`), `coverage_periods` (`_id` = `uuid5(case_id, "coverage")`), `outbox` (`_id` = `uuid5(case_id, notice_type)`), and the `AuditLogEntry` (`action=caseworker_action`, `target_type=case`, success/refused) in `benefit_audit`; duplicate key = already applied; tests in `tests/apps/worker/repositories/test_cases.py` (depends on T006) (ADR-001-01, ADR-001-06; FR-001-04, FR-001-10, FR-001-20, FR-001-22)
- [X] T012 [US1] [workflows] [benefit-be] Create thin activity `record_case_change` (`CaseChange` → `None`, policy `DEFAULT` from `apps/worker/policies.py`) in `apps/worker/activities/case_record.py` calling `repositories/cases.py`; builds the scope from the change's `case_id`/`household_id`; never logs `reason` text (PL-11); tests in `tests/apps/worker/activities/test_case_record.py` (depends on T011) (TW-9, TW-11; FR-001-04, FR-001-10)
- [X] T013 [US1] [workflows] [benefit-be] Create `CaseWorkflow` in `apps/worker/workflows/case.py` (input `CaseStart`, result final `CaseStatus`): submitted → verifying on start, call `verify_documents` (`AGENT_STEP`), → determining, call `determine_eligibility` with `as_of_date = case_today_wf`, `eligible` → decided/approved with coverage + `approval` notice in the same `record_case_change`; `ineligible`/`cannot_determine` → under_review with a review task (`adverse_determination` with failed rules / `cannot_determine` listing `missing_items`), then `workflow.wait_condition` on the `caseworker_action` signal; `approve_denial` → decided/denied with `denial_reason` from the determination + `denial` notice; `override_to_approve` (reason required) → decided/approved with `override {reviewer_id, reason, determination_id}`, determination untouched; disallowed action or state → `action_rejected` event; duplicate `request_id` ignored (set of applied IDs, R10); every change a `CaseEvent` with `seq`, `case_time` and `real_time`; `cannot_determine` never decides; uses `workflow.now()` only (depends on T008–T012) (ADR-001-01, ADR-001-04; FR-001-02, FR-001-07, FR-001-09, FR-001-10, FR-001-13, FR-001-16, FR-001-20, FR-001-22)
- [X] T014 [US1] [workflows] [benefit-be] Add queries to `CaseWorkflow` in `apps/worker/workflows/case.py`: `allowed_actions` → `AllowedActions {task_id, actions}` or empty, and `status` → `CaseStatus` with `open_review_task` (depends on T013) (ADR-001-04; FR-001-07, FR-001-02)
- [X] T015 [US1] [workflows] [benefit-be] Register `CaseWorkflow`, `record_case_change`, `verify_documents`, `determine_eligibility` in `apps/worker/main.py`; extend `tests/apps/worker/test_main.py` (depends on T010, T012, T013) (FR-001-03)
- [X] T016 [US1] [workflows] [benefit-be] Time-skipping workflow tests with stubbed activities in `tests/apps/worker/workflows/test_case.py`: `test_FR_001_16_eligible_decides_approved`, `test_FR_001_09_ineligible_waits_for_approve_denial`, `test_FR_001_16_cannot_determine_opens_task_never_decides`, `test_FR_001_20_override_keeps_determination`, `test_FR_001_02_disallowed_action_recorded_rejected`, `test_FR_001_04_duplicate_request_id_ignored`, `test_FR_001_13_events_carry_case_and_real_time` (TW-13, TW-15) (FR-001-02, FR-001-04, FR-001-09, FR-001-10, FR-001-13, FR-001-16, FR-001-20)

### Data lane

- [X] T038 [P] [US1] [data] [benefit-be] Before T017: write failing TC-29 in `tests/db/seeds/test_reset.py` (every stub result present, synthetic households only; PR-3, BA-11) (FR-001-16)
- [X] T017 [P] [US1] [data] [benefit-be] Add a synthetic per-household stub field (verification and determination result: `eligible` | `ineligible` | `cannot_determine`) to the demo seed in `db/seeds/generate.py` and `db/seeds/reset.py` so `make dev` can drive every path; tests in `tests/db/seeds/test_reset.py` (PR-3; FR-001-16)

### Platform & UI lane (ADR-001-05 Option A)

- [X] T039 [P] [US1] [platform-ui] [benefit-be] Before T019: write failing TC-50–TC-57 in `tests/apps/api/services/test_cases.py` with a fake repository, fake Temporal client and fixed clock (FR-001-01, FR-001-13, FR-001-23)
- [X] T040 [US1] [platform-ui] [benefit-be] Before T020, T021: write failing TC-58 in `tests/apps/api/routers/test_applications.py` and TC-59–TC-63 in `tests/apps/api/routers/test_cases.py` via `TestClient` + `dependency_overrides`, incl. every rejected role (PL-7) and no reason text in logs (PL-11) (FR-001-01, FR-001-07, FR-001-09, FR-001-20)
- [X] T018 [P] [US1] [platform-ui] [benefit-be] Create `apps/api/repositories/cases.py` (scoped reads of `cases`, `coverage_periods`; guarded insert) and `apps/api/schemas/cases.py` (`ApplicationSubmission`, `ReviewActionBody` with `reason` maxLength 500, `CaseStatus`) matching `contracts/rest-api.openapi.yaml` (depends on T006) (FR-001-01, FR-001-23)
- [X] T019 [US1] [platform-ui] [benefit-be] Create `apps/api/services/cases.py` `submit_application`: `case_id = case_id_for(ref)`; one transaction — existing case → return it (200); `coverage_periods` with `end_date >= case_today` → refuse `household_has_coverage`; insert case (`state: submitted`, `open: true`, `received_on` = `case_today`, `decision_deadline` = +45, `clock` with scale 1 or 1440 from `DEMO_PROFILE`); duplicate key on the partial index → refuse `household_has_open_case`; then start `CaseWorkflow` with ID `case-{case_id}` via `apps/api/temporal_client.py`, already-started = success, Temporal down → 503; household from `Principal` only; tests in `tests/apps/api/services/test_cases.py` (depends on T018) (ADR-001-02, ADR-001-03; FR-001-01, FR-001-13, FR-001-23)
- [X] T020 [US1] [platform-ui] [benefit-be] Create `apps/api/routers/applications.py` `POST /api/v1/applications` (role applicant; 201 / 200 / 409 `error.code=conflict` with reason in `error.fields[0].type` / 401 / 403 / 503) and register it in `apps/api/main.py`; tests in `tests/apps/api/routers/test_applications.py` (depends on T019) (FR-001-01, FR-001-23)
- [X] T021 [US1] [platform-ui] [benefit-be] Create `apps/api/routers/cases.py` `POST /api/v1/cases/{case_id}/review-tasks/{task_id}/actions` (role caseworker or supervisor): 422 when `override_to_approve` lacks `reason`; pre-check the `allowed_actions` query, 409 if not allowed (the workflow still records the rejection); else signal `caseworker_action` with `reviewer_id` from `Principal`, 202; register in `apps/api/main.py`; tests in `tests/apps/api/routers/test_cases.py` (depends on T014, T018) (ADR-001-04; FR-001-07, FR-001-09, FR-001-20)
- [X] T022 [US1] [contracts] [benefit-be] Regenerate `openapi/openapi.json` with `make openapi` after T020, T021 and T027, confirm it matches `contracts/rest-api.openapi.yaml`, and run `make test-contract` (`tests/contract/test_openapi.py`, `tests/contract/test_every_route_protected.py`) (completes T004) (FR-001-01, FR-001-11, FR-001-23)

**Checkpoint**: US1 works end to end with stubs (quickstart steps 1–5).

---

## Phase 4: User Story 2 - Case survives restarts (Priority: P1)

**Goal**: A case interrupted by a worker restart resumes at the same step, with no repeated task, event, finding or notice.

**Independent Test**: Stop the worker mid-verification and while waiting on a review task, restart, and confirm the case continues with no duplicate effects (quickstart step 6).

- [X] T041 [P] [US2] [workflows] [benefit-be] Add failing TC-49 `test_FR_001_04_restart_after_approval_requests_no_second_notice` in `tests/apps/worker/workflows/test_case_restart.py` (US2-AS2; TW-16); T023 = TC-46, T024 = TC-47, TC-48, T025 = TC-18 (FR-001-04)
- [X] T023 [P] [US2] [workflows] [benefit-be] Record happy-path and override histories into `tests/apps/worker/histories/case_approved.json` and `tests/apps/worker/histories/case_override.json` and add `test_FR_001_03_case_replay` in `tests/apps/worker/workflows/test_case_replay.py` following `test_smoke_replay.py` (TW-14, R9; SC-001-05) (FR-001-03)
- [X] T024 [P] [US2] [workflows] [benefit-be] Add `test_FR_001_03_restart_mid_verification` and `test_FR_001_03_restart_while_waiting_on_task_no_second_task` in `tests/apps/worker/workflows/test_case_restart.py` following `test_smoke_restart.py` (TW-16; SC-001-01, SC-001-05) (FR-001-03, FR-001-04)
- [X] T025 [P] [US2] [workflows] [benefit-be] Add `test_FR_001_04_record_case_change_retry_is_noop` in `tests/apps/worker/repositories/test_cases.py`: the same `CaseChange` applied twice yields one event, one task, one coverage period, one outbox record, one audit entry (ADR-001-01; SC-001-01) (FR-001-04)

**Checkpoint**: US1 and US2 both pass; `make test-workflow` green.

---

## Phase 5: User Story 3 - Deadline visibility (Priority: P3)

**Goal**: Caseworkers see days remaining to the 45-day deadline and an at-risk flag at 10 or fewer days.

**Independent Test**: Cases at different case-clock ages show the right days remaining; a 36-day-old undecided case shows 9 days and at risk.

- [X] T042 [P] [US3] [workflows] [benefit-be] Before T026: write failing TC-44, TC-45 in `tests/apps/worker/workflows/test_case.py` (FR-001-11)
- [X] T043 [P] [US3] [platform-ui] [benefit-be] Before T027: write failing TC-64, TC-65 in `tests/apps/api/routers/test_cases.py` (PL-7: other household → 404) (FR-001-11)
- [X] T026 [P] [US3] [workflows] [benefit-be] Compute `days_remaining` (= `decision_deadline - case_today_wf`, null once decided) and `at_risk` (`days_remaining <= 10`) in the `status` query of `apps/worker/workflows/case.py`; `test_FR_001_11_day_36_shows_9_remaining_at_risk` in `tests/apps/worker/workflows/test_case.py` (R3; no timer) (FR-001-11, FR-001-18)
- [X] T027 [P] [US3] [platform-ui] [benefit-be] Create `GET /api/v1/cases/{case_id}` in `apps/api/routers/cases.py` and `get_case_status` in `apps/api/services/cases.py`: read the case scoped to the caller (applicant own household only, caseworker, supervisor; else 404), compute `days_remaining`/`at_risk` from the stored `clock` with `case_today` (same rule as T026), add `open_review_task` from the `review_tasks` projection; tests including `test_FR_001_11_*` in `tests/apps/api/routers/test_cases.py` (depends on T018) (ADR-001-03; FR-001-11, FR-001-13)

**Checkpoint**: all three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T028 [P] [workflows] [benefit-be] Check `CaseWorkflow` determinism: no I/O, settings or `datetime.now()` in `apps/worker/workflows/`; workflow imports only `packages/domain` and `packages/platform/clock` (TW-1, TW-2); run `make lint typecheck test-unit test-workflow` (FR-001-03)
- [X] T029 [P] [platform-ui] [benefit-be] Confirm no log line in `apps/api/services/cases.py` or `apps/api/routers/cases.py` contains `reason` text or household data (PL-11, constitution VIII) (FR-001-20)
- [X] T030 [contracts] [benefit-be] Run `make check` and walk `specs/001-case-lifecycle/quickstart.md` steps 1–7 against `make dev` (including `DEMO_PROFILE=true` for step 7) (FR-001-01, FR-001-03, FR-001-11, FR-001-13, FR-001-23)

---

## Phase 7: QA (cross-lane, after all lanes finish)

- [X] T044 [qa] [benefit-be] Contract tests TC-66, TC-67 in `tests/contract/test_case_lifecycle_contract.py`: generated OpenAPI matches `contracts/rest-api.openapi.yaml`; registered workflow, signal, query and activity names match `contracts/case-workflow.md` (after T022) (FR-001-01, FR-001-07, FR-001-11, FR-001-23)
- [X] T045 [qa] [benefit-be] Concurrency integration TC-68, TC-69 in `tests/integration/test_case_submission.py` (parallel submissions, real MongoDB + Temporal dev server; ADR-001-02) (FR-001-23)
- [X] T046 [qa] [benefit-be] Cross-database audit transaction TC-70 in `tests/integration/test_case_audit.py` (verifies R7) (FR-001-10)
- [X] T047 [qa] [benefit-be] Journey integration TC-71–TC-74, TC-76, TC-77 in `tests/integration/test_case_journey.py`: API → worker → MongoDB for approved, denied, override, cannot-determine, status agreement and demo-profile history (FR-001-01, FR-001-09, FR-001-11, FR-001-13, FR-001-16, FR-001-20, FR-001-22)
- [X] T048 [qa] [benefit-be] Real worker restart TC-75 in `tests/integration/test_case_restart.py`: kill the worker process mid-case, restart, count events, tasks and outbox records (SC-001-01; TW-16) (FR-001-03, FR-001-04)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)** → **Contracts step (T002–T004)** → **Lane foundations (T005–T008)** → user stories → polish.
- US1 must land before US2 (US2 tests the US1 workflow) and before US3's workflow part (T026 extends T014). T027 depends only on T018.

### Within US1

- Workflows: T009, T010, T011 in parallel → T012 → T013 → T014 → T015 → T016.
- Platform & UI: T018 → T019 → T020; T018 + T014 → T021; all → T022.
- Data: T017 independent.

### Parallel Opportunities

- T005, T006, T007 run in parallel (three lanes); T008 after T005.
- In US1 the three lanes run in parallel: workflows (T009–T016), data (T017), platform-ui (T018–T021).
- US2 T023–T025 in parallel; US3 T026 and T027 in parallel.

## Parallel Example: User Story 1

```bash
Task: "T009 case_states.py transition table and helpers"           # [workflows]
Task: "T010 verify_documents / determine_eligibility stubs"          # [workflows]
Task: "T011 apps/worker/repositories/cases.py transaction"          # [workflows]
Task: "T017 seed stub field"                                         # [data]
Task: "T018 apps/api repositories and schemas for cases"            # [platform-ui]
```

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 + Phase 2 (contracts merged first).
2. Phase 3 (US1), then validate with quickstart steps 1–5.

### Incremental Delivery

1. US1 → MVP demo of submission to decision.
2. US2 → durability guarantee (replay + restart on every PR, SC-001-05).
3. US3 → deadline visibility.

## Notes

- FR coverage: FR-001-01 (T003, T007, T009, T019, T020), FR-001-02 (T002, T009, T013, T016), FR-001-03 (T015, T023, T024), FR-001-04 (T007, T011, T012, T016, T025), FR-001-07 (T013, T014, T021), FR-001-09 (T013, T016, T021), FR-001-10 (T011, T012, T013), FR-001-11 (T026, T027), FR-001-13 (T005, T008, T013, T019), FR-001-16 (T002, T010, T013, T016), FR-001-18 (T005, T009, T026), FR-001-20 (T011, T013, T021), FR-001-22 (T006, T009, T013), FR-001-23 (T006, T007, T019, T020).
- The quality engineer adds the test plan and the cross-lane `[qa]` integration tasks (submission guards under concurrency, cross-database audit transaction R7, end-to-end with MongoDB + Temporal) next.
- Commit inside `repos/benefit-be` on `feature/001-case-lifecycle`.
