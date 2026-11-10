# Contract: CaseWorkflow review interface (010)

Provider: Workflows (`repos/benefit-be/apps/worker/`). Consumers: Platform & UI (006 API), 007, 011, 008 (reads the collections). Payload models: `packages/domain/review.py` (data-model.md).

## Signal

| Name | Payload | Sent by | Behaviour |
|---|---|---|---|
| `caseworker_action` | `CaseworkerActionSignal` | `apps/api` (006) after auth (PL-6) and a pre-check against `ALLOWED_ACTIONS` | Queued; processed in order. Duplicate `action_id` ignored. Applied or rejected and recorded (ADR-010-02). |

## Queries

| Name | Returns | Use |
|---|---|---|
| `open_review_tasks` | `list[ReviewTaskState]` | Tests and diagnostics; the queue itself reads `review_tasks` (ADR-010-01). |

## Internal entry point (other Workflows features)

`open_review(reason, cause, evidence_refs, *, coverage_end=None) -> UUID`: a workflow-level helper in `apps/worker/workflows/review.py` that 001, 007 and 011 call to open a task. Blocking reasons then wait until the task closes; `explanation_review` returns immediately.

## Activities (Workflows provides and uses)

| Activity | Preset | Input | Idempotency |
|---|---|---|---|
| `upsert_review_task` | `DEFAULT` | `ReviewTask` | upsert by `_id` |
| `set_review_flag` | `DEFAULT` | `task_id, flag, at_case` | update only where `status: open` |
| `close_review_task` | `DEFAULT` | `task_id, action_id` | update only where `status: open` |
| `record_caseworker_action` | `DEFAULT` | `CaseworkerAction` | unique `action_id`; with `eval_overrides` in one transaction for AI overrides (research R6) |

## Interfaces used (stubbed until ready)

- 001: `CaseWorkflow`, case states, `case_events` recording, decision deadline.
- 011: case-clock helper (case-clock instant ↔ real duration), advance-clock signal, response-window timer, `notice_drafts` revisions.
- 002: `verify_documents`, `draft_request`. 003: `evaluate`. 004: explanation check result. 007: coverage end date.
