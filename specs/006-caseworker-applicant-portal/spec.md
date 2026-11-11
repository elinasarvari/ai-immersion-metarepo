# Feature Specification: Caseworker Console and Applicant Portal (retired)

**Feature Branch**: `feature/006-caseworker-applicant-portal`

**Created**: 2026-11-09

**Status**: Retired (2026-11-10)

## Why it was retired

This feature held every screen of the product, while the features that provide the data and
operations behind those screens were backend only. Nothing was visible in the browser until
almost every feature was built, and no feature could be checked end to end through its screens.

Each screen now lives in the feature whose operations it uses, so every feature is built and
tested from the screen down. The rules every screen follows moved to 000.

## Moved user stories

| Was | Now |
|---|---|
| US1 Caseworker works the review queue | 010 US4; correcting the income check is 002 US6 |
| US2 Caseworker approves notices | 011 US4 |
| US3 Applicant applies and uploads documents | 001 US4 (the form), 002 US5 (pay stubs) |
| US4 Applicant sees status, requests and history | 001 US5 (status), 011 US5 (requests), 004 US5 (history), 007 US5 (renewals) |
| US5 Applicants see only their own records | FR-000-31, tested on every screen; 001 US5 scenario 2 |

## Moved requirements

IDs are not reused. References elsewhere point to the new IDs.

| Old ID | Now | Topic |
|---|---|---|
| FR-006-01 | FR-010-07, FR-010-08 | Review queue and task screen |
| FR-006-02 | FR-002-19 | Correcting a pay stub detail or dismissing a finding, with a reason |
| FR-006-03 | FR-001-26 (status), FR-011-10 (open requests) | Applicant's view on sign-in |
| FR-006-04 | FR-004-16 | Applicant's past decisions with explanations |
| FR-006-05 | FR-000-31 | Household isolation on every screen |
| FR-006-06 | FR-011-08 | Notice approval |
| FR-006-07 | FR-001-24 (form), FR-002-17 (pay stub upload) | Application |
| FR-006-08 | FR-011-10 (request for information), FR-007-19 (redetermination) | Applicant responses |
| FR-006-09 | FR-001-27 (states, history), FR-002-18 (documents, findings), FR-003-23 (determinations), FR-004-15 (explanations), 010 and 011 (actions, notices) | Case page |
| FR-006-10 | FR-000-30 | WCAG 2.1 AA |
| FR-006-11 | FR-000-29 | Synthetic data banner |
| FR-006-12 | FR-010-08 | Task already actioned |
| FR-006-13 | FR-011-11 | Advance clock button |
| FR-006-14 | Removed (2026-11-11, no AI in the MVP) | AI activity |
| FR-006-15 | FR-011-09 | Applicant's notices |
| FR-006-16 | FR-007-17 (deferred) | Upcoming redeterminations |
| FR-006-17 | FR-007-18 | Start a redetermination from the household page |
| FR-006-18 | FR-001-25 | Refused application with a link to the open case |
| SC-006-01 | SC-010-05 | Review in under 2 minutes |
| SC-006-02 | SC-001-06, SC-002-06 | Apply with a pay stub in under 5 minutes |
| SC-006-03 | SC-000-10 | Cross-household access refused |
| SC-006-04 | SC-000-11 | Automated accessibility check |

Edge cases moved with their stories: "already actioned by …" to 010, upload limits to 002, a
session expiring mid-form to 001, keyboard and screen reader use to 000.
