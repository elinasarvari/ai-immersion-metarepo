# ADR-001-02: Open the case in one guarded transaction, then start the workflow by a derived ID

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-01, FR-001-23, US1-1, US1-6
- **Lanes affected:** Platform & UI | Workflows | Knowledge & data
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

FR-001-23 needs two guarantees: the same submission reference opens one case, and a household with an open case or an unended coverage period is refused **with the reason** (US1-6), which the applicant must see at submit time. Two submissions can race. TW-3 asks for a workflow ID derived from the case ID, so starting twice is idempotent. The API starts workflows (PL-2) and the worker may not be called directly (BA-5). Checks done only in code are racy; `database.md` asks for integrity in the database (unique indexes). Who builds the endpoint is ADR-001-05; this ADR fixes the mechanism either way.

## Options

### Option A: API transaction with database guards, then start by derived ID
`case_id = uuid5(SUBMISSION_NS, submission_reference)`. A service in `apps/api/services/cases.py` runs one transaction: if `cases._id == case_id` exists, return it (idempotent); if `coverage_periods` holds a period for the household with `end_date >= today` (case clock) refuse `household_has_coverage`; insert the case with `open: true`. A partial unique index `cases(household_id) where open: true` refuses a concurrent second case (`household_has_open_case`). Then `start_workflow(CaseWorkflow, id=f"case-{case_id}")`; an already-started error is treated as success. If the start fails, the client retries the same submission, finds the case and starts again.
- **Pros:** synchronous refusal with reason; race-safe by index; idempotent at both steps.
- **Cons:** the API writes the first case document, the worker every later change (two writers, separated in time).

### Option B: Workflow's first activity opens the case
The API only starts `case-{uuid5(ref)}`; activity `open_case` applies the same guards and the workflow ends as "Refused".
- **Pros:** one writer.
- **Cons:** the refusal is asynchronous, so the API must poll or wait on the workflow (an anti-pattern, capabilities §2); every refused submission leaves a workflow execution.

### Option C: Temporal update-with-start
Start and validate in one call.
- **Pros:** one round trip, synchronous result.
- **Cons:** still needs DB guards in an activity; support in the dev server version installed by the Brewfile is unverified; TW-5 names signals.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-001-01, -23) | Yes | Refusal is late | Yes |
| Constitution and rules (TW-3, PL-2, BA-5, KD-10) | Yes | Yes | Unverified |
| Simplicity (X) | High | Medium | Low |
| Security and privacy | Household from `Principal` | Same | Same |
| Testability | API integration test | Workflow test | Needs server feature |
| Fits existing code | `apps/api/temporal_client.py:66` | Yes | No precedent |
| Reversibility | High | High | Medium |
| Effort | Small | Small | Unknown |

## Decision

We choose **Option A**: the database enforces both duplicate rules and the derived workflow ID makes the start idempotent, while the applicant gets the reason synchronously. The case document the API inserts is the `Submitted` state; from then on only the workflow changes it (ADR-001-01).

## Consequences

- **Good:** US1-6 holds under concurrency; no polling.
- **Bad / accepted trade-offs:** a case can briefly exist with no workflow if the start fails; the retried submission or a startup sweep (not in scope) starts it. Coverage check reads "today" from the case clock rules of ADR-001-03.
- **Work this creates:** Knowledge & data: partial unique index and `submission_reference` unique index in `0002_case_lifecycle`. Platform & UI: `services/cases.py`, `repositories/cases.py` (only if ADR-001-05 keeps the endpoint in 001). Workflows: `CaseWorkflow` input `CaseStart`. Contracts: `ApplicationSubmission`, `SubmissionRefused` reason enum.

## How we verify it

Integration tests: the same reference twice gives one case and one workflow; two concurrent submissions for one household give one case and one `household_has_open_case` refusal; an active coverage period refuses (CI). Code review checks no code path inserts into `cases` without the transaction.

## References

FR-001-01, FR-001-23; TW-3, TW-5; PL-2; BA-5; KD-10; `database.md`; capabilities §2, §3.
