# Architecture decisions: 003-eligibility-rules

## Needs a decision
- none

## Decided automatically (review in the PR)
- ADR-003-06: How much completed history (FR-003-22) to seed before 004, 007 and 011 define their stores? → Option A (seeds every store on main without 003 defining other lanes' contracts, VI/BA-8; explanations and other notices as files for 004/011)
- ADR-003-07: How to merge main (001, 010) into the branch? → Option A (migration renumbered to 0005 on main's 0003 `households` validator; A/B/C are three of the 200 households; 001 stub fields kept until T023/T011)

## Proposed – needs amendment
- none

## Decisions
| ADR | Title | Status | Lanes | Repos |
|---|---|---|---|---|
| [ADR-003-01](ADR-003-01-rule-sets-as-versioned-code.md) | Rule sets are versioned code; the database holds a seeded copy | Accepted | Knowledge & data | benefit-be |
| [ADR-003-02](ADR-003-02-determination-contract-and-activity.md) | The activity stores the full determination; the workflow keeps 001's summary | Accepted | Knowledge & data, Workflows, Platform & UI | benefit-be |
| [ADR-003-03](ADR-003-03-snapshot-capture-and-interim-verifications.md) | Snapshot capture in the worker, with seeded verifications until 002 and 005 land | Accepted | Knowledge & data, Workflows | benefit-be |
| [ADR-003-04](ADR-003-04-align-with-main-definitions.md) | Reuse main's definitions; renumber the 003 migration after main's | Accepted | all (shared domain) | benefit-be |
| [ADR-003-05](ADR-003-05-determinations-read-api-and-section.md) | A determinations sub-resource and its own case page section | Accepted | Platform & UI | benefit-be, benefit-fe |
| [ADR-003-06](ADR-003-06-completed-history-seeding-scope.md) | Completed-history seeding scope | Accepted – auto-decided | Knowledge & data | benefit-be |
| [ADR-003-07](ADR-003-07-align-with-main.md) | Merging main (001, 010) into the 003 branch | Accepted – auto-decided | Knowledge & data | benefit-be |

## For research.md
- Rule IDs and policy refs: ELIG-01…06, TM-2.1…TM-3.1 (stable, pinned by contract snapshot) — R1
- Money: Decimal, stub income to the cent, limit floored to the dollar, stored as strings — R2
- Case outcome mapping: ELIG-06 → income_over_limit, others → other_rule_not_met — R5
- Deterministic IDs: uuid5 of case and as-of date, stub's formula kept — R6
- Form → snapshot mapping for new households — R8
- Frontend query key and section registry — R12
