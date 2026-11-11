# ADR-010-04: Retry limit comes from the activity RetryPolicy; terminal failure opens a review task

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-03, SC-010-02, FR-002-04
- **Lanes affected:** Workflows
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

When verification or determination fails after 3 attempts, a review task must be created instead of stalling (FR-010-03). The worker already has `AGENT_STEP` with `maximum_attempts=3` and `DEFAULT` with `maximum_attempts=5` (`benefit-be:apps/worker/policies.py:23-43`), and marks `ValidationError`, `PermissionDenied`, `CredentialRejected` non-retryable (`policies.py:15`). FR-002-04 is separate: three unresolved verification *loops* inside the agent end in a finding, not an exception.

## Options

### Option A: RetryPolicy does the counting
Verification uses `AGENT_STEP` (3 attempts); determination gets a new preset `RULES_STEP` with `maximum_attempts=3`. The workflow wraps each call in `try/except ActivityError`, and on any terminal failure opens a review task with `cause` `retry_limit_reached` or `non_retryable_error`, then waits.
- **Pros:** no extra workflow state; one place sets the limit; history records each attempt.
- **Cons:** non-retryable errors go to review after one attempt (Recommendation: correct, since retrying them can't help and the spec's aim is "no stall").

### Option B: Workflow loop with single-attempt activities
`maximum_attempts=1` and a workflow counter up to 3.
- **Cons:** duplicates Temporal's retry with backoff in workflow code; more history events; breaks the `policies.py` convention that every call uses a preset with retries (TW-10).

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (FR-010-03, SC-010-02) | Yes | Yes |
| Constitution and rules | TW-10 | Bends TW-10 |
| Simplicity (X) | High | Low |
| Security and privacy | Same | Same |
| Testability | Stub raises → assert task | Same |
| Fits existing code | `policies.py` presets | New pattern |
| Reversibility | High | High |
| Effort | Low | Medium |

## Decision

We choose **Option A**. Which review reason a determination failure uses is open in ADR-010-05; until it's decided the code uses its recommendation behind one constant.

## Consequences

- **Good:** SC-010-02 holds for any failure type, not just exhausted retries.
- **Bad / accepted trade-offs:** the agent-step model budget stays 3 × (1 + `LLM_MAX_RETRIES`) calls (`policies.py:3-5`).
- **Work this creates:** [workflows] `RULES_STEP` preset, failure handling around verification and determination calls, `ReviewCause` values in evidence.

## How we verify it

- Workflow tests with stubs that always raise (retryable and non-retryable): a review task appears after attempt 3 / attempt 1, and the workflow is waiting, not failed (SC-010-02).
- Unit test: `RULES_STEP.retry_policy.maximum_attempts == 3`.

## References

TW-9, TW-10, TW-15; `benefit-be:apps/worker/policies.py`; FR-002-04, FR-010-03; ADR-010-05.
