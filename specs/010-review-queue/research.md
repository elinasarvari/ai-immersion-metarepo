# Research: 010 Review queue and caseworker actions

Date: 2026-11-10. Significant choices are ADRs in `decisions/`; these are the smaller ones.

## R1. One automatic request for information per case (FR-010-04)
- **Decision:** `CaseWorkflow` state holds `auto_rfi_used: bool`. Automatic drafting (from a verification finding, 002) is skipped once it is `True`; the case opens a Verification review instead. Caseworker "Request information" actions never check or set it.
- **Reason:** workflow state is durable and replay-safe (constitution II); no extra read.
- **Alternatives:** count `notice_drafts` per case with an activity (extra I/O, race with drafting).

## R2. "Extend by 15 days" once per request (FR-010-01, edge case)
- **Decision:** `extended_request_ids: set[UUID]` in workflow state; a second extension for the same `request_id` is rejected with `extension_already_used`.
- **Reason:** same as R1. The new deadline itself is 011's response-window timer (FR-011-01).
- **Alternatives:** a flag on the notice draft (owned by 011, cross-lane write).

## R3. Evidence by reference
- **Decision:** `ReviewTask.evidence_refs` holds typed references (`finding_id`, `determination_id`, `notice_draft_id`, `explanation_id`, `request_id`) plus a `cause` code; no free text, no document values.
- **Reason:** keeps workflow history small (capabilities §4 red flag) and personal data out of history and logs (constitution VIII, PL-11).
- **Alternatives:** inline evidence snapshot (large history, personal data in Temporal).

## R4. Where the worker's MongoDB code lives
- **Decision:** `apps/worker/repositories/review_tasks.py` and `caseworker_actions.py`, called by thin activities (TW-9). Each query includes `household_id` and `case_id` from the system credential (database.md, constitution VIII).
- **Reason:** database.md names "the repository modules in … `apps/worker/`"; workflows never import them (TW-2).
- **Alternatives:** `packages/platform` (forbidden: no business logic there, `backend-architecture.md` layout).

## R5. Edit actions carry a revision reference
- **Decision:** "Edit and approve" (Notice approval, Explanation review) carries `revision_id` of a draft revision already saved by the API through 011's `notice_drafts` contract; the workflow records both IDs ("both kept").
- **Reason:** signal payloads stay small and contain no applicant text.
- **Alternatives:** edited text in the signal (personal data in history).

## R6. Overrides of AI output feed evaluations (FR-002-11, constitution IV)
- **Decision:** "Correct a value" and "Dismiss a finding" activities also insert an `eval_overrides` record in the same transaction as the `caseworker_actions` record (database.md multi-document rule).
- **Reason:** one atomic write; `eval_overrides` already exists (`benefit-be:db/migrations/versions/0001_baseline.py:50`).
- **Alternatives:** a later export job (can drift).

## R7. Override to approve (FR-001-20)
- **Decision:** the stored `Determination` is never changed; the case outcome records `override_action_id`, reviewer and reason. Constitution I holds: a person, not AI, overrides.

## R8. Rejected actions recorded
- **Decision:** rejected actions are written to `caseworker_actions` with `outcome: rejected` and a `RejectionCode`, plus an `audit_log` entry `caseworker_action` / `refused` (`benefit-be:packages/domain/audit.py:14,29`).
- **Reason:** FR-010-05 and FR-001-10 with the existing audit model; no new audit action needed.
