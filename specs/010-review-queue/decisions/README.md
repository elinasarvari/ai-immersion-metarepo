# Architecture decisions: 010-review-queue

## Needs your decision
- None.

## Proposed – needs amendment
- None.

## Decisions
| ADR | Title | Status | Lanes | Repos |
|---|---|---|---|---|
| ADR-010-01 | CaseWorkflow owns review tasks; `review_tasks` is a projection | Accepted | Workflows, Knowledge & data, Platform & UI | benefit-be |
| ADR-010-02 | Caseworker actions: one signal with idempotency key, shared action table | Accepted | Workflows, Platform & UI | benefit-be |
| ADR-010-03 | Reminder and escalation as per-task Temporal timers on the case clock | Accepted | Workflows | benefit-be |
| ADR-010-04 | Retry limit from the activity RetryPolicy; terminal failure opens review | Accepted | Workflows | benefit-be |
| ADR-010-05 | Review reason for a failed determination | Accepted | Workflows | benefit-be |
| ADR-010-06 | How review days are counted | Accepted | Workflows | benefit-be |

## For research.md
- One automatic request per case (FR-010-04): `auto_rfi_used: bool` in workflow state (R1).
- Extension once per request: `extended_request_ids` in workflow state (R2).
- Evidence by reference, not inline (R3).
- Worker repository location `apps/worker/repositories/` (R4).
- Notice and explanation edit actions carry a draft revision reference, not text (R5).
