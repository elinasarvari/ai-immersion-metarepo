---

description: "Task list for 010 Review queue and caseworker actions"
---

# Tasks: Review Queue and Caseworker Actions

**Input**: Design documents from `specs/010-review-queue/` (plan.md, spec.md, research.md, data-model.md, contracts/workflow-review.md, decisions/ADR-010-01 … 06)

**Target repo**: `repos/benefit-be` only (plan.md). No `benefit-fe` tasks: the queue screens and the action endpoint are 006.

**Tests**: test-first and `[qa]` tasks are added by the quality engineer from `test-plan.md` (test-strategy skill).

**Tags**: every task carries one lane (`[contracts]`, `[workflows]`, `[data]`) and its repo (`[benefit-be]`), and the FR IDs it serves. `[contracts]` covers shared changes only (`packages/domain/`, settings and `.env.example`); every other task touches only its lane's folders (`apps/worker/` for Workflows, `db/` for Knowledge & data).

**Rules to read before each task**: `[workflows]` → `project-rules/temporal-workflows.md`; `[data]` → `data-knowledge.md`, `database.md`; `[contracts]` → `backend-architecture.md` (plus `platform-api.md` for `packages/platform/`). Always: `backend-python.md`, `security.md`, `testing.md`.

**Decisions**: ADR-010-05 (reason for a failed determination) and ADR-010-06 (how review days are counted) are Accepted with Option A (2026-11-10), which is what the tasks build, each behind one constant.

**Other features' FRs** this work touches (stubbed or old IDs, not built here): FR-001-08, FR-001-12, FR-001-19, FR-001-21 (old IDs of FR-010-02, FR-010-03, FR-010-01, FR-010-04), FR-001-10 (action recording, T012), FR-001-13 (case clock, T017), FR-001-20 (T012), FR-002-11 and FR-006-02 (AI overrides, T006), FR-004-11 and FR-011-02 (raising points, T013), FR-007-04 (coverage end, T016/T017), FR-011-04 (demo time scale, T017).

## Format: `[ID] [P?] [Story] [lane] [repo] Description (FRs)`

---

## Phase 1: Setup (shared contracts)

**Purpose**: the Day 1 contracts PR every lane builds against (constitution VI).

### Tests first (write, see them fail, then T001/T002)

- [X] T020 [contracts] [benefit-be] Write TC-01, TC-02, TC-03 in `tests/packages/domain/test_review.py` (action table, `REASON_REQUIRED`/`AI_OVERRIDES`/`BLOCKING`, signal reason 1–500 and `extra="forbid"`). Before T001. (FR-010-01, FR-010-05)
- [X] T021 [P] [contracts] [benefit-be] Write TC-39 in `tests/packages/platform/test_settings.py` (defaults 2 and 4, escalation must be after reminder). Before T002. (FR-010-02)

### Implementation

- [X] T001 [contracts] [benefit-be] Create `packages/domain/review.py` (Pydantic v2, `extra="forbid"`, UUID IDs, UTC datetimes): enums `ReviewReason` (`adverse_determination`, `cannot_determine`, `notice_approval`, `verification_review`, `missed_response_deadline`, `explanation_review`), `ActionType` (11 values), `ReviewCause` (15 values), `ReviewTaskStatus` (`open`, `closed`), `ReviewFlag` (`reminder`, `escalated`), `ActionOutcome` (`applied`, `rejected`), `RejectionCode` (`not_allowed_for_reason`, `reason_required`, `task_closed`, `extension_already_used`); the data tables `ALLOWED_ACTIONS: Mapping[ReviewReason, frozenset[ActionType]]`, `REASON_REQUIRED = {override_to_approve, correct_value, dismiss_finding, extend_15_days, continue_with_held_data}`, `AI_OVERRIDES = {correct_value, dismiss_finding}`, `BLOCKING` (all reasons except `explanation_review`), exactly as in data-model.md "Action table"; models `EvidenceRef` (`{kind, id}` only, R3), `CorrectedValue` (`field_ref`, `value`), `ReviewTask` (all fields in data-model.md; `reminder_at`, `escalated_at`, `coverage_end`, `closed_by_action_id` "null" allowed), `ReviewTaskState` (same minus `created_at`/`updated_at`), `CaseworkerActionSignal` (`reason: str | None` "1–500 chars, required for REASON_REQUIRED"; `submitted_at` real time), `CaseworkerAction` (signal fields plus `household_id`, `case_id`, `outcome`, `rejection_code`, `applied_at_case`, `recorded_at`). Export from `packages/domain/__init__.py`. (FR-010-01, FR-010-05, FR-010-06)
- [ ] T002 [P] [contracts] [benefit-be] Add settings `REVIEW_REMINDER_DAYS` (default 2) and `REVIEW_ESCALATION_DAYS` (default 4, must be > reminder) to `packages/platform/settings.py` and `.env.example` (ADR-010-03, spec "Project values"). (FR-010-02)

**Checkpoint**: contracts PR merged; lanes start in parallel.

---

## Phase 2: Foundational (blocking prerequisites)

### Tests first

- [X] T022 [P] [data] [benefit-be] Write TC-35, TC-36, TC-37, TC-38 in `tests/db/migrations/test_0002_review_queue.py` (validator rejects unknown reason and extra fields, unique `action_id`, down restores baseline, queue queries use the indexes). Before T003. (FR-010-01, FR-010-02, FR-010-06)
- [X] T023 [P] [workflows] [benefit-be] Write TC-24 in `tests/apps/worker/test_policies.py` (`RULES_STEP` 3 attempts). Before T004. (FR-010-03)
- [X] T024 [P] [workflows] [benefit-be] Write TC-19, TC-20 in `tests/apps/worker/repositories/test_review_tasks.py` and TC-10, TC-17, TC-18 in `tests/apps/worker/repositories/test_caseworker_actions.py` (integration marker, local MongoDB, two synthetic households). Before T005, T006. (FR-010-01, FR-010-02, FR-010-05, FR-010-06)
- [X] T025 [workflows] [benefit-be] Write TC-40, TC-41 in `tests/apps/worker/activities/test_review_tasks.py` (fake repositories; reason never logged; idempotent upsert). Before T007. (FR-010-01, FR-010-05)
- [X] T026 [workflows] [benefit-be] Write TC-04 in `tests/apps/worker/workflows/test_review.py` against `ReviewHarnessWorkflow` with stubbed activities (TW-15). Before T008, T009. (FR-010-01)

### Implementation

- [X] T003 [P] [data] [benefit-be] Write migration `db/migrations/versions/0002_review_queue.py`: full `$jsonSchema` validators for `review_tasks` and `caseworker_actions` matching data-model.md (`additionalProperties: false`, required `household_id`, `case_id`, enum values from T001); indexes `review_tasks {status: 1, decision_deadline: 1}`, `{status: 1, flags: 1, decision_deadline: 1}`, `caseworker_actions` unique `{action_id: 1}` and `{task_id: 1, recorded_at: 1}`; down migration restores the `0001_baseline` minimal validators and drops these indexes. (FR-010-01, FR-010-02, FR-010-06)
- [X] T004 [P] [workflows] [benefit-be] Add `RULES_STEP` preset to `apps/worker/policies.py` (`maximum_attempts=3`, `NON_RETRYABLE_ERRORS`, timeout per TW-10) (ADR-010-04). (FR-010-03)
- [X] T005 [P] [workflows] [benefit-be] Create `apps/worker/repositories/__init__.py` and `apps/worker/repositories/review_tasks.py`: `upsert(task)` by `_id`; `set_flag(task_id, flag, at_case)` and `close(task_id, action_id)` that update only where `status: "open"`; every query filtered by `household_id` and `case_id` (R4, constitution VIII). (FR-010-01, FR-010-02)
- [X] T006 [P] [workflows] [benefit-be] Create `apps/worker/repositories/caseworker_actions.py`: `record(action)` insert relying on unique `action_id` (duplicate key = already recorded, return existing); for `action` in `AI_OVERRIDES` insert the `eval_overrides` record in the same transaction (R6); for `outcome: rejected` also write `audit_log` `caseworker_action` / `refused` (R8, `packages/domain/audit.py`); never log `reason` (PL-11). (FR-010-01, FR-010-05, FR-010-06)
- [X] T007 [workflows] [benefit-be] Create thin activities in `apps/worker/activities/review_tasks.py` — `upsert_review_task`, `set_review_flag`, `close_review_task`, `record_caseworker_action` — calling T005/T006 (TW-9), and register them in `apps/worker/main.py`. Depends on T005, T006. (FR-010-01, FR-010-02, FR-010-05)
- [X] T008 [workflows] [benefit-be] Create `apps/worker/workflows/review.py` core (no DB imports, TW-2): `ReviewState` (open tasks by `task_id`, `seen_action_ids: set[UUID]`, `auto_rfi_used: bool`, `extended_request_ids: set[UUID]`); `open_review(reason, cause, evidence_refs, *, coverage_end=None) -> UUID` that builds the task with `workflow.uuid4()`, sets `blocking` from `BLOCKING`, upserts via `upsert_review_task` (`DEFAULT` preset), and waits until closed for blocking reasons (returns at once for `explanation_review`); `caseworker_action` signal handler that queues payloads; `open_review_tasks` query returning `list[ReviewTaskState]` (contracts/workflow-review.md). Depends on T001, T007. (FR-010-01)
- [X] T009 [workflows] [benefit-be] Create stubs for interfaces not yet built in `apps/worker/workflows/review_ports.py`: case-state transition hook and `case_events` recording (001), case-clock helper and advance-clock signal (011), `verify_documents`/`draft_request` (002), `evaluate` (003), coverage end date (007), each behind a small protocol so `CaseWorkflow` swaps in the real one; plus a minimal `ReviewHarnessWorkflow` in `apps/worker/workflows/review_harness.py` that composes `review.py` until 001 lands (plan "Open questions"). (FR-010-01, FR-010-02, FR-010-03)

**Checkpoint**: tasks can be opened, projected and queried; user stories can proceed in parallel.

---

## Phase 3: User Story 1 - Caseworker resolves a review task (P2) 🎯 MVP

**Goal**: every reason offers exactly its actions; allowed actions resume the case with the listed result; everything else is refused and recorded; each action applies once.

**Independent Test**: raise each of the six reasons in `ReviewHarnessWorkflow`, confirm `open_review_tasks` and the allowed set, send each action, confirm the result and the `caseworker_actions` record.

### Tests first

- [X] T027 [P] [US1] [workflows] [benefit-be] Write TC-06, TC-08, TC-13, TC-16 in `tests/apps/worker/workflows/test_review_validate.py` (pure `validate_action`, parametrized). Before T010. (FR-010-01, FR-010-05)
- [X] T028 [US1] [workflows] [benefit-be] Write TC-07, TC-09 in `tests/apps/worker/workflows/test_review.py` (rejected recorded and task open; same `action_id` twice applied once). Before T011. (FR-010-05, FR-010-06)
- [X] T029 [US1] [workflows] [benefit-be] Write TC-05, TC-11, TC-12, TC-14, TC-15 in `tests/apps/worker/workflows/test_review.py` (all 16 allowed pairs and their results, override keeps determination, caseworker request after auto request, edit keeps both, explanation non-blocking). Before T012, T013. (FR-010-01, FR-010-04)

### Implementation

- [X] T010 [US1] [workflows] [benefit-be] Add pure `validate_action(task, signal, state) -> RejectionCode | None` in `apps/worker/workflows/review.py`: `task_closed` if not open; `not_allowed_for_reason` if `signal.action not in ALLOWED_ACTIONS[task.reason]`; `reason_required` if action in `REASON_REQUIRED` and `reason` is missing; `extension_already_used` if `extend_15_days` for a `request_id` in `extended_request_ids` (R2). (FR-010-01, FR-010-05)
- [X] T011 [US1] [workflows] [benefit-be] Add idempotent processing loop in `apps/worker/workflows/review.py`: process queued signals in order; skip any `action_id` already in `seen_action_ids`; record rejected actions via `record_caseworker_action` with `outcome: rejected` and the code, task stays open. Depends on T010. (FR-010-05, FR-010-06)
- [X] T012 [US1] [workflows] [benefit-be] Map each allowed `(reason, action)` to its result in `apps/worker/workflows/review.py` through the 001 transition hook (T009), as in FR-010-01 "Actions and result": approve denial → Decided/Denied; override to approve → Decided/Approved with `override_action_id`, reviewer and reason, stored determination unchanged (R7, FR-001-20); request information → `draft_request` (never checks or sets `auto_rfi_used`, R1); correct value / dismiss finding → Determining with the change; accept findings → Determining; approve / edit and approve → sent, keeping both draft and `revision_id` (R5); deny for missing information → Decided/Denied (redetermination: coverage ended by caseworker decision); extend by 15 days → Awaiting applicant, add `request_id` to `extended_request_ids`; continue with held data → Determining. Then `record_caseworker_action` (`applied`, `applied_at_case`) and `close_review_task`. Depends on T011. (FR-010-01, FR-010-04, FR-010-06)
- [X] T013 [US1] [workflows] [benefit-be] Add raising points in `ReviewHarnessWorkflow` (`apps/worker/workflows/review_harness.py`) for each reason with its cause and evidence refs: Ineligible → `adverse_determination`/`ineligible`; Cannot determine → `cannot_determine`/`cannot_determine`; notice ready → `notice_approval`/`notice_ready`; verification findings → `verification_review` with the finding's cause; missed window → `missed_response_deadline`/`response_deadline_missed`; failed explanation checks → `explanation_review`/`explanation_check_failed` (non-blocking). Depends on T012. (FR-010-01)

**Checkpoint**: US1 works end to end in the harness.

---

## Phase 4: User Story 2 - Stuck work goes to a person (P2)

**Goal**: verification and determination failures past the retry limit open a review task; the case never stalls; at most one automatic request for information.

**Independent Test**: stub `verify_documents` / `evaluate` to always raise; after attempt 3 (retryable) or 1 (non-retryable) a review task is open and the workflow is waiting, not failed.

### Tests first

- [X] T030 [US2] [workflows] [benefit-be] Write TC-21, TC-22, TC-23, TC-25 in `tests/apps/worker/workflows/test_review_failures.py` (stubs that always raise, retryable and non-retryable; attempt counts; second automatic request). Before T014, T015. (FR-010-03, FR-010-04)

### Implementation

- [X] T014 [US2] [workflows] [benefit-be] Add `run_or_review(...)` in `apps/worker/workflows/review.py`: call `verify_documents` with `AGENT_STEP` and `evaluate` with `RULES_STEP`; on `ActivityError` open a review with cause `retry_limit_reached` or `non_retryable_error` (from the cause's type) — verification → `verification_review`; determination → `DETERMINATION_FAILURE_REASON = cannot_determine` with cause `determination_failed` (one constant, ADR-010-05 recommendation A). Depends on T008, T004. (FR-010-03)
- [X] T015 [US2] [workflows] [benefit-be] Add the one-automatic-request rule in `apps/worker/workflows/review.py`: automatic drafting from a verification finding calls `draft_request` only while `auto_rfi_used` is `False`, then sets it; afterwards opens a `verification_review` task instead (R1). Depends on T008. (FR-010-04)

**Checkpoint**: US2 works with failing stubs; no workflow ends in failure.

---

## Phase 5: User Story 3 - Overdue tasks are reminded and escalated (P2)

**Goal**: tasks open 2 days get `reminder`, 4 days or past coverage end (redetermination) get `escalated`, on the case clock.

**Independent Test**: open a task, advance the case clock 2 then 4 days, check `flags` on the projection and in `open_review_tasks`.

### Tests first

- [X] T031 [P] [US3] [workflows] [benefit-be] Write TC-26, TC-27 in `tests/apps/worker/workflows/test_review_timers.py` (2-day boundary, earlier of 4 days and coverage end, UTC). Before T016. (FR-010-02)
- [X] T032 [US3] [workflows] [benefit-be] Write TC-28, TC-29, TC-30, TC-31, TC-32 in `tests/apps/worker/workflows/test_review_flags.py` (time-skipping reminder, escalation, coverage end, action wins at timer instant, advance-clock). Before T017. (FR-010-02)

### Implementation

- [X] T016 [P] [US3] [workflows] [benefit-be] Create pure functions in `apps/worker/workflows/review_timers.py`: `reminder_due(opened_at_case, settings)`, `escalation_due(opened_at_case, coverage_end, settings)` (earlier of 4 days and coverage end), using elapsed case-clock time behind one constant `REVIEW_DAY_COUNTING = "elapsed"` (ADR-010-06 recommendation A). (FR-010-02)
- [X] T017 [US3] [workflows] [benefit-be] Add per-task timers in `apps/worker/workflows/review.py` (ADR-010-03): on open, start reminder and escalation waits converted through the case-clock helper (T009, demo time scale FR-011-04), re-evaluated on advance-clock; on fire, if the task is still open, set the flag in state and call `set_review_flag`; if the task closed first, do nothing (edge case "action wins"). Depends on T016, T008. (FR-010-02)

**Checkpoint**: all three stories work in the harness.

---

## Phase 6: Polish & cross-cutting

- [X] T033 [workflows] [benefit-be] Record `tests/apps/worker/histories/review_v1.json` (open, reminder, action) and write TC-33 in `tests/apps/worker/workflows/test_review_replay.py` (TW-14) and TC-34 in `tests/apps/worker/workflows/test_review_restart.py` (TW-16). After T017. (FR-010-01, FR-010-02)

- [ ] T018 [workflows] [benefit-be] When 001's `CaseWorkflow` exists, compose `review.py` into `apps/worker/workflows/case.py` (signal, query, raising points from T013, `run_or_review` from T014) and replace the 001/002/003/007/011 stubs in `review_ports.py` as each lands; keep `ReviewHarnessWorkflow` for tests. (FR-010-01 … FR-010-04)
- [ ] T019 [workflows] [benefit-be] Check `review.py`, activities and repositories log no free-text `reason`, corrected values or applicant data (PL-11, constitution VIII), and run quickstart.md steps 1–5 including `make check`. (FR-010-01 … FR-010-06)

---

## Phase 7: QA (cross-lane, after all lanes join)

- [X] T034 [qa] [benefit-be] Write TC-46 in `tests/contract/test_review_contract.py`: signal `caseworker_action`, query `open_review_tasks` and payload models match contracts/workflow-review.md and `packages/domain/review.py`. (FR-010-01)
- [X] T035 [qa] [benefit-be] Write TC-42, TC-43, TC-45 in `tests/integration/test_review_queue.py` (Temporal dev server + MongoDB with migration 0002, stubbed agents, seed household via BA-11): Ineligible case → `adverse_determination` task in `review_tasks`; signal twice → one `applied` record; failing verification → task projected. (FR-010-01, FR-010-03, FR-010-06)
- [X] T036 [qa] [benefit-be] Write TC-44 in `tests/integration/test_review_queue.py`: `DEMO_PROFILE=true`, `reminder` after 2 minutes and `escalated` after 4 in `review_tasks.flags` (quickstart step 4, FR-011-04). (FR-010-02)

---

## Dependencies & Execution Order

- Tests first: each `Tests first` task (T020–T032) runs before the implementation task it names and must fail first (constitution V). T033 after T017. QA tasks T034–T036 after every lane task and T018 where available.
- Phase 1 (T001, T002) blocks everything. T003 (data) and T004–T006 (workflows) run in parallel after it.
- T007 needs T005, T006. T008 needs T001, T007. T009 needs T008.
- US1 (T010 → T011 → T012 → T013), US2 (T014, T015) and US3 (T016 → T017) all need Phase 2 and then run in parallel; they share `review.py`, so merge in order T010–T012, T014–T015, T017 or split into separate functions per story.
- T018 depends on 001 landing; T019 last.

## Parallel Examples

```text
After T001/T002:  T003 [data]  |  T004  |  T005  |  T006
After Phase 2:    US1 (T010…)  |  US2 (T014, T015)  |  US3 (T016 → T017)
```

## Implementation Strategy

1. MVP: Phases 1–3 (US1): every reason has its exact actions, refused actions recorded, idempotent.
2. Add US2 (no stalls), then US3 (reminder kept; the escalation flag is the third cut if behind, specs/README.md).
3. T018 once 001 merges; T019 before the PR.
