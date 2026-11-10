# Architecture decisions: 001-case-lifecycle

## Needs a decision
- (none)

## Decided automatically (review in the PR)
- ADR-001-04: Caseworker actions as validated updates or signals? → Option B, signals plus `allowed_actions` pre-check query (within TW-5; amendment to allow updates left as a suggestion for the team)
- ADR-001-05: Does 001 ship `POST /applications`, `GET /cases/{id}` and the review-action endpoint (no UI), or does 006? → Option A, 001 ships them (only option that proves FR-001-23/US1-6 and the US1-5 pre-check within 001, per ADR-001-02 and ADR-001-04)

## Proposed – needs amendment
- (none; ADR-001-04's TW-5 amendment is kept under its "Amendment suggested" section)

## Decisions
| ADR | Title | Status | Lanes | Repos |
|---|---|---|---|---|
| ADR-001-01 | CaseWorkflow owns the state; MongoDB holds an idempotent projection | Accepted | Workflows, Knowledge & data | benefit-be |
| ADR-001-02 | Open the case in one guarded transaction, then start the workflow by a derived ID | Accepted | Platform & UI, Workflows, Knowledge & data | benefit-be |
| ADR-001-03 | Case clock as parameters on the case, computed from workflow time | Accepted | Workflows, Platform & UI | benefit-be |
| ADR-001-04 | Caseworker actions as validated updates instead of signals | Accepted – auto-decided | Workflows, Platform & UI | benefit-be |
| ADR-001-05 | 001 or 006 ships the case endpoints | Accepted – auto-decided | Platform & UI, Workflows | benefit-be |
| ADR-001-06 | A case-bound worker scope for activity database access | Accepted | Platform & UI, Workflows | benefit-be |

## For research.md
- Verification/determination stubs: stub activities in `apps/worker/activities/` behind the agreed names (002, 003 replace the body).
- At-risk flag: computed on read from the stored deadline and `case_today`, no timer (nothing happens at the threshold in 001).
- Coverage period: computed in a pure helper from the case-clock receipt date; written in the `Decided` transaction.
- Caseworker action audit: `record_case_change` writes the `audit_log` entry in the same transaction (cross-database transaction on the replica set).
- Denial reason precedence: taken from the determination (FR-003-20); the workflow does not re-derive it.
