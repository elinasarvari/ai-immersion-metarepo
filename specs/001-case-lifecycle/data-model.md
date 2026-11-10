# Data model: 001 Case lifecycle

Shared models go in `repos/benefit-be/packages/domain/` (BA-6, BA-8) in the contracts step. Storage is MongoDB database `benefit` (KD-9); validators and indexes go in migration `db/migrations/versions/0002_case_lifecycle.py` (KD-11), tightening the minimal validators of `0001_baseline.py`. All instants are UTC BSON dates; dates are Chicago calendar dates (`database.md`, FR-000-27). IDs are UUIDs.

## Enums (`packages/domain/case.py`)

| Enum | Values | Source |
|---|---|---|
| `CaseType` | `application`, `redetermination` | TW-6 (001 builds `application` only) |
| `CaseState` | `submitted`, `verifying`, `awaiting_applicant`, `determining`, `under_review`, `decided` | FR-001-02 |
| `CaseOutcome` | `approved`, `denied` (+ `renewed_automatically`, `renewed_after_response`, `ended_by_caseworker` reserved for 007) | FR-001-16, specs/README.md |
| `DenialReason` | `income_over_limit`, `other_rule_not_met`, `missing_information` | FR-001-16 |
| `ReviewReason` | `adverse_determination`, `cannot_determine`, `notice_approval`, `verification_review`, `missed_response_deadline`, `explanation_review` | FR-010-01 (full list now, so 010 adds no contract change) |
| `CaseworkerActionType` | `approve_denial`, `override_to_approve`, `request_information`, `correct_value`, `dismiss_finding`, `accept_findings`, `approve`, `edit_and_approve`, `deny_for_missing_information`, `extend_15_days`, `continue_with_held_data` | FR-010-01; 001 handles only the first two |
| `CaseEventKind` | `state_changed`, `review_task_opened`, `caseworker_action`, `action_rejected`, `notice_requested`, `coverage_started`, `demo_action` | FR-001-10, FR-001-05 |
| `DeterminationOutcome` | `eligible`, `ineligible`, `cannot_determine` | owned by 003 (minimal shape below) |
| `SubmissionRefusal` | `household_has_open_case`, `household_has_coverage` | FR-001-23 |
| `CoverageStatus` | `active`, `continued_pending_review`, `renewed`, `ended` | spec Key Entities, 007 |

## Models

**CaseClock** (ADR-001-03): `real_start: datetime`, `case_start: datetime`, `scale: int` (1, or 1440 in the demo profile), `offset_seconds: int = 0` (changed only by 011).

**CaseStart** (workflow input): `case_id`, `household_id`, `case_type`, `submission_reference`, `received_at` (case clock), `clock: CaseClock`.

**Case** (`cases`): `_id` (= `uuid5(SUBMISSION_NS, submission_reference)`), `household_id`, `case_id` (= `_id`, for the scope filter), `case_type`, `submission_reference` (unique), `state`, `open: bool` (false once `decided`), `received_on: date`, `decision_deadline: date` (= `received_on` + 45, FR-001-01), `clock: CaseClock`, `outcome: CaseOutcome | null`, `denial_reason | null`, `override: {reviewer_id, reason, determination_id} | null` (FR-001-20), `decided_on: date | null`, `last_seq: int`, `created_at`, `updated_at`.
- Indexes: unique `submission_reference`; partial unique `household_id` where `open: true` (ADR-001-02); `(state, decision_deadline)` for the console's deadline sort (006).

**CaseEvent** (`case_events`): `_id`, `case_id`, `household_id`, `seq: int`, `kind: CaseEventKind`, `from_state | null`, `to_state | null`, `case_time: datetime`, `real_time: datetime` (FR-001-13), `actor_type` (`system` | `user`), `actor_id | null`, `reason_code: str` (enum-backed, no free text), `review_task_id | null`, `created_at`.
- Indexes: unique `(case_id, seq)` (ADR-001-01, FR-001-04).

**ReviewTask** (`review_tasks`): `_id` (workflow-generated), `case_id`, `household_id`, `reason: ReviewReason`, `evidence: {determination_id | null, missing_items: list[str], failed_rules: list[str]}`, `allowed_actions: list[CaseworkerActionType]`, `status` (`open`, `resolved`), `opened_case_time`, `opened_real_time`, `reminder: bool = false`, `escalated: bool = false` (set by 010), `resolution: {action, reviewer_id, reason | null, case_time} | null`.
- Indexes: `(status, opened_real_time)` for the shared queue (010).

**CaseworkerActionRequest** (signal payload; API body): `task_id`, `action: CaseworkerActionType`, `reviewer_id`, `reason: str | null` (required for `override_to_approve`, max 500 chars, never logged), `request_id`.

**CaseworkerAction** (`caseworker_actions`): `_id` (= `request_id`, idempotent), `case_id`, `household_id`, `task_id`, `action`, `reviewer_id`, `reason | null`, `outcome` (`applied`, `rejected`), `case_time`, `real_time`.

**CoveragePeriod** (`coverage_periods`): `_id` (= `uuid5(case_id, "coverage")`), `household_id`, `case_id`, `start_date` (first day of the receipt month, case clock), `end_date` (last day of the 12th month), `status: CoverageStatus` (FR-001-22). Index: `(household_id, end_date)` for the FR-001-23 check.

**HouseholdStubResult** (`household_stub_results`, household-only scope, 001 stub only): `_id` (= `household_id`), `household_id`, `stub_result: DeterminationOutcome`. Seeded from the same values as `households.stub_result`, so the worker's `determine_eligibility` stub reads it under its household-bound scope without reading `households` (ADR-001-06, research R1). Unique index `household_id`. 003 drops it with the stub.

**Notice request** (`outbox`): `_id` (= `uuid5(case_id, notice_type)`), `case_id`, `household_id`, `notice_type` (`approval`, `denial` for 001; full enum from FR-011-06), `status: requested`, `requested_case_time`. Delivery is 011.

**Determination (minimal, owned by 003)**: `determination_id`, `outcome: DeterminationOutcome`, `reason_code: DenialReason | null`, `missing_items: list[str]`, `as_of_date: date`. 001 reads only these fields; the stored determination is never changed (FR-001-20).

**CaseChange** (input of `record_case_change`): `case_id`, `household_id`, `seq`, `event: CaseEvent` fields, optional `case_update`, optional `review_task` (open or resolve), optional `action: CaseworkerAction`, optional `coverage: CoveragePeriod`, optional `notice: notice request`. All written in one transaction (KD-10), with the audit entry for caseworker actions (`AuditAction.caseworker_action`, `packages/domain/audit.py`).

**CaseStatus** (query result and API response): `case_id`, `state`, `received_on`, `decision_deadline`, `days_remaining: int | null` (null once decided), `at_risk: bool` (`days_remaining <= 10`, FR-001-11), `outcome`, `denial_reason`, `open_review_task: {task_id, reason, allowed_actions} | null`.

## State transitions (`apps/worker/workflows/case_states.py`, FR-001-02)

| From | To | Trigger | Feature |
|---|---|---|---|
| submitted | verifying | workflow start | 001 |
| verifying | determining | verification complete | 001 (stub), 002 |
| verifying | awaiting_applicant | request for information | 011 |
| verifying | under_review | verification needs review | 010 |
| awaiting_applicant | verifying | applicant response | 011 |
| awaiting_applicant | under_review | missed deadline | 011 |
| determining | decided (approved) | determination `eligible` | 001 |
| determining | under_review | `ineligible` or `cannot_determine` (FR-001-09, FR-001-16) | 001 |
| under_review | decided (denied) | `approve_denial` | 001 |
| under_review | decided (approved, override) | `override_to_approve` + reason | 001 |
| under_review | determining / awaiting_applicant | other FR-010-01 actions | 010 |

Anything else is refused and recorded as `action_rejected` (FR-001-05). `decided` is terminal.
