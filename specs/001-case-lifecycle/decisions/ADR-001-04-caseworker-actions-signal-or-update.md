# ADR-001-04: Caseworker actions as validated Temporal updates instead of signals

- **Status:** Accepted – auto-decided
- **Date:** 2026-11-10
- **Feature:** specs/001-case-lifecycle/ · **Requirements:** FR-001-05 (US1-5), FR-001-07, FR-001-09, FR-001-20; FR-010-01 (consumer)
- **Lanes affected:** Workflows | Platform & UI
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

US1-5: a transition not allowed from the current state is refused **and** recorded as a rejected action. A caseworker who picks an action the task doesn't allow (010) should learn it at once. TW-5 says caseworker actions arrive as **signals**; a signal returns nothing to the sender, so the API cannot tell the caller the action was refused. Temporal workflow updates have a validator and return a result; temporalio 1.35.0 is pinned (`repos/benefit-be/pyproject.toml:15`), but whether the installed Temporal dev server enables updates by default is unverified (check on 2026-11-10 pending).

## Options

### Option A: Updates (needs a TW-5 amendment)
`@workflow.update submit_action(CaseworkerActionRequest) -> ActionResult` with a `@validator` that checks the task is open and the action allowed for its reason. Rejected calls never enter history, so the rejection is recorded by the API in `caseworker_actions` with `outcome: rejected`.
- **Pros:** synchronous accept/refuse; no polling.
- **Cons:** needs TW-5 changed; server support to verify.

### Option B: Signals plus a pre-check query (fallback, within TW-5)
The API first queries `allowed_actions` (TW-5 query), refuses invalid requests with 409 and records them through the repository; valid ones are sent as the `caseworker_action` signal. The workflow re-checks on receipt, and if the state changed in between it records the rejection via `record_case_change` (kind `action_rejected`).
- **Pros:** within the rules; works on any server.
- **Cons:** a small race window where the API says "accepted" and the workflow then rejects; rejection then shows in history, not in the response.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets the spec (US1-5) | Yes | Yes, with a race window |
| Constitution and rules (TW-5) | Needs amendment | Yes |
| Simplicity (X) | High | Medium |
| Testability | Time-skipping test of validator | Query + signal tests |
| Reversibility | Medium | High |
| Effort | Small, plus server check | Small |

## Decision

We choose **Option B: Signals plus a pre-check query (fallback, within TW-5)**.

- **Amendment (never amend):** Option A needs TW-5 changed, which only all three team members can do (Governance). B is the compliant fallback; the proposed wording is kept below under "Amendment suggested".
- **Rules and constitution:** B satisfies TW-5 as written (signals for actions, `allowed_actions` as a query) and constitution II (deterministic workflow re-checks the action on receipt) and IV (rejected actions are recorded).
- **Spec:** B meets US1-5 and FR-001-05: invalid requests get a 409 from the API pre-check and are recorded; the rare race case is refused by the workflow and recorded as `action_rejected`, so every refused transition is still "refused and recorded as a rejected action".
- **Missing evidence:** update support on the installed dev server is unverified (check pending since 2026-11-10); B works on any server and is the easier to reverse, since the payload (`CaseworkerActionRequest`) is the same for both transports.
- The plan, contracts and tasks already assume B, so no re-plan is needed. The architect's proposal was A conditional on the amendment, with B as the fallback in use; I agree with B under the current rules.

**Decided by:** decision-maker (automated), 2026-11-10; architect recommended Option B (fallback in use; Option A proposed pending a TW-5 amendment)
**Revisit if:** the team amends TW-5 to allow updates with a validator and a spike confirms updates work on the installed Temporal dev server, or tests show the signal race window producing rejections a caller should have seen in the response.

## Amendment suggested

Rule TW-5, current wording: "Caseworker actions arrive as signals. Read-only state is exposed through queries." Proposed wording: "Caseworker actions arrive as signals, or as updates with a validator when the caller needs the result. Read-only state is exposed through queries." Changing a rule set needs all three team members (Governance). If amended, switch to Option A: only the transport changes (same `CaseworkerActionRequest` model), after a spike verifies updates on the installed dev server.

## Consequences

- **Good:** one payload model (`CaseworkerActionRequest`) for both transports.
- **Bad / accepted trade-offs:** with B, a race can surface a rejection only in case history.
- **Work this creates:** Workflows: signal handler and `allowed_actions` query in `case.py`. Platform & UI: action endpoint pre-check (ADR-001-05). Contracts: `CaseworkerActionRequest`, `AllowedActions`.

## How we verify it

Time-skipping tests: an invalid action via signal produces an `action_rejected` event and no state change; the API returns 409 for an action not in `allowed_actions` (CI). If amended: verify updates work on the installed dev server (spike).

## References

TW-4, TW-5; constitution II, IV, Governance; FR-001-05, FR-010-01.
