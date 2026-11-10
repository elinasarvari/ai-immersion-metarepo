# ADR-010-02: Caseworker actions are one signal with an idempotency key; the workflow validates against a shared action table

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/010-review-queue/ · **Requirements:** FR-010-01, FR-010-05, FR-010-06, FR-006-12
- **Lanes affected:** Workflows | Platform & UI
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

Each reason allows a fixed set of actions, some needing a reason (FR-010-01). Disallowed or reason-less actions must be refused and recorded (FR-010-05); duplicates applied once (FR-010-06, constitution II "never apply a caseworker action twice"). TW-5 says caseworker actions arrive as **signals** with `packages/domain` payloads. The API (006) must also tell a second caseworker "already actioned by …" (FR-006-12). Signals are fire-and-forget, so the API can't get the workflow's verdict synchronously.

## Options

### Option A: Signal + shared table + API pre-check
`packages/domain/review.py` holds `ALLOWED_ACTIONS: Mapping[ReviewReason, frozenset[ActionType]]` and `REASON_REQUIRED: frozenset[ActionType]` (data only, BA-6). The API validates against the table and the projection (task open?), then sends `caseworker_action(CaseworkerActionSignal)` with a client-generated `action_id`. The workflow is authoritative: it re-checks the table, the task's state and `seen_action_ids`; applies or rejects; and records either through `record_caseworker_action` (unique index on `action_id`).
- **Pros:** within TW-5; the API refuses the common cases at once; races are resolved in single-threaded workflow code.
- **Cons:** two caseworkers racing both get `202 Accepted`; the loser sees "rejected: already actioned" on refresh.

### Option B: Temporal Workflow Update with a validator
Same table; the API calls an Update and gets accept/reject synchronously.
- **Pros:** exact synchronous answer.
- **Cons:** contradicts TW-5 ("signals") → needs a rule amendment; Update support on the local dev server is unverified for this project's pinned versions.

### Option C: Validate only in the API
- **Cons:** the API reads a lagging projection (ADR-010-01), so a race can apply two actions; breaks FR-010-06.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-010-05/06, FR-006-12) | Yes (async loser) | Yes | No (FR-010-06) |
| Constitution and rules | II, TW-5 | Needs TW-5 amendment | Breaks II |
| Simplicity (X) | High | Medium | High |
| Security and privacy | API auth per PL-6, workflow re-checks | Same | Weak |
| Testability | Time-skipping signal tests | Same | – |
| Fits existing code and ADRs | ADR-010-01 | ADR-010-01 | Conflicts ADR-010-01 |
| Reversibility | High (B later) | Medium | – |
| Effort | Low | Medium | Low |

## Decision

We choose **Option A**: it satisfies every FR within TW-5 today, and moving to Option B later only changes the transport, not the table or the records.

## Consequences

- **Good:** one table drives the API, the workflow and the tests (SC-010-01 can be parametrised over it).
- **Bad / accepted trade-offs:** the race loser's refusal is visible only after the workflow records it.
- **Work this creates:**
  - [contracts] `ActionType`, `ALLOWED_ACTIONS`, `REASON_REQUIRED`, `CaseworkerActionSignal`, `CaseworkerAction`, `ActionOutcome` (`applied`, `rejected`) with `RejectionCode` (`not_allowed_for_reason`, `reason_required`, `task_closed`, `extension_already_used`, `missing_required_field`, `request_draft_failed`).
  - [workflows] signal handler (queue only, no awaits), action processing in the main loop, `record_caseworker_action` activity.
  - [data] unique index `caseworker_actions.action_id`.
  - 006 (Platform & UI) uses the table for its pre-check and returns `202`.

## How we verify it

- Parametrised workflow test over every `(reason, action)` pair: allowed → listed result; disallowed → `rejected/not_allowed_for_reason` (FR-010-01, FR-010-05).
- Workflow test: the same `action_id` signalled twice → one `applied` record (FR-010-06); a crash test between apply and record (TW-16).
- Integration test: inserting the same `action_id` twice is a no-op (TW-11).

## References

TW-5, TW-11, TW-16, BA-6, BA-8, PL-6; constitution II, IV; FR-006-12.
