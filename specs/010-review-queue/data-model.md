# Data model: 010 Review queue and caseworker actions

All models are Pydantic v2 in `repos/benefit-be/packages/domain/review.py` (BA-6, BA-8), `extra="forbid"`, IDs as UUID, times as UTC datetimes (database.md). They go in the Day 1 contracts PR (constitution VI); 001 owns the base `ReviewTask` shape (spec Key Entities) and this feature fills in reasons, actions and flags.

## Enums

- `ReviewReason`: `adverse_determination`, `cannot_determine`, `notice_approval`, `verification_review`, `missed_response_deadline`, `explanation_review` (FR-010-01).
- `ActionType`: `approve_denial`, `override_to_approve`, `request_information`, `correct_value`, `dismiss_finding`, `accept_findings`, `approve`, `edit_and_approve`, `deny_missing_information`, `extend_15_days`, `continue_with_held_data`.
- `ReviewCause` (evidence): `low_confidence`, `unreadable_document`, `different_person`, `identity_mismatch`, `income_source_mismatch`, `missing_citation`, `verification_unavailable`, `retry_limit_reached`, `non_retryable_error`, `determination_failed`, `ineligible`, `cannot_determine`, `notice_ready`, `response_deadline_missed`, `explanation_check_failed`.
- `ReviewTaskStatus`: `open`, `closed`.
- `ReviewFlag`: `reminder`, `escalated`.
- `ActionOutcome`: `applied`, `rejected`. `RejectionCode`: `not_allowed_for_reason`, `reason_required`, `task_closed`, `extension_already_used`, `missing_required_field`, `request_draft_failed`.

## Action table (data, FR-010-01)

`ALLOWED_ACTIONS: Mapping[ReviewReason, frozenset[ActionType]]`

| Reason | Allowed | Blocks the decision |
|---|---|---|
| adverse_determination | approve_denial, override_to_approve*, request_information | yes |
| cannot_determine | request_information, correct_value* | yes |
| notice_approval | approve, edit_and_approve | yes (the notice) |
| verification_review | accept_findings, correct_value*, dismiss_finding*, request_information | yes |
| missed_response_deadline | deny_missing_information, extend_15_days*, continue_with_held_data* | yes |
| explanation_review | approve, edit_and_approve | **no** |

`REASON_REQUIRED = {override_to_approve, correct_value, dismiss_finding, extend_15_days, continue_with_held_data}` (the * actions). `AI_OVERRIDES = {correct_value, dismiss_finding}` (FR-010-01, R6).

## ReviewTask (stored in `review_tasks`; projection, ADR-010-01)

| Field | Type | Notes |
|---|---|---|
| `_id` / `task_id` | UUID | `workflow.uuid4()` |
| `household_id`, `case_id` | UUID | required (database.md) |
| `workflow_id` | str | |
| `reason` | ReviewReason | |
| `cause` | ReviewCause | |
| `evidence_refs` | list[EvidenceRef] | `{kind, id}` only (R3) |
| `blocking` | bool | from table |
| `status` | ReviewTaskStatus | |
| `opened_at_case`, `opened_at_real` | datetime | case clock and real (FR-001-13) |
| `reminder_at`, `escalated_at` | datetime \| null | case clock when set |
| `flags` | list[ReviewFlag] | |
| `decision_deadline` | date | for queue sort (FR-006-01) |
| `coverage_end` | date \| null | redetermination tasks only (FR-010-02) |
| `closed_by_action_id` | UUID \| null | |
| `created_at`, `updated_at` | datetime | real time |

`ReviewTaskState` is the in-workflow view (same fields minus storage timestamps).

## CaseworkerActionSignal (signal payload, TW-5)

`action_id: UUID` (client idempotency key), `task_id: UUID`, `action: ActionType`, `reviewer_id: UUID`, `reviewer_role: Role`, `reason: str | None` (1–500 chars, required for REASON_REQUIRED), `corrected_value: CorrectedValue | None` (`field_ref`, `value`), `finding_id: UUID | None`, `revision_id: UUID | None`, `submitted_at: datetime` (real time from the API).

## CaseworkerAction (stored in `caseworker_actions`)

Signal fields plus `household_id`, `case_id`, `outcome`, `rejection_code`, `applied_at_case`, `recorded_at`. `reason` is free text written by staff: never logged (PL-11).

## State changes per action

Listed in FR-010-01 ("Actions and result"); the workflow maps each `(reason, action)` to the next case state (001) and records it in `case_events` (FR-001-10).

## MongoDB (migration `0002_review_queue`, Knowledge & data)

- `review_tasks`: full `$jsonSchema` from the table above, `additionalProperties: false`. Indexes: `{status: 1, decision_deadline: 1}` (queue), `{status: 1, flags: 1, decision_deadline: 1}` (escalated view), existing `case_created`.
- `caseworker_actions`: full `$jsonSchema`; unique `{action_id: 1}`; `{task_id: 1, recorded_at: 1}`.
- Down migration restores the baseline minimal validators and drops these indexes.
