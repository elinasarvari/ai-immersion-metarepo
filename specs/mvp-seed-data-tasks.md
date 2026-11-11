# MVP seed data tasks

Drafted 2026-11-11. The MVP specs assume data that the 003 data set on `main` doesn't have yet.
The tasks below add it.

- **Lane and repo:** `[data]`, `benefit-be/db/seeds/` and `db/migrations/` (Knowledge & data owns
  both).
- **Who:** the 002 / 004a seat, since 002 and 004a need it first. S-01 to S-03 come before 002's
  check can be tested. S-04 and S-05 are needed by 007 and 008, and can land in phase 1 while
  those seats build against fixtures.
- **Rules:** synthetic data only, marked per store (FR-000-14). Every value comes from the seed
  and the data set's anchor date, never the wall clock (FR-003-22). The generator stays
  deterministic, so running it twice gives the same manifest hashes (SC-003-03).

## What is missing today

| Spec needs | On `main` | Gap |
|---|---|---|
| FR-002-22, FR-007-13: identity record and per-job reference income, with some disagreements | `seeded_verifications` sets `identity_verified=True` for everyone; "mismatch" only means declared versus pay stub income | No reference records, no identity disagreements, no reference income that differs from held income, no job the household didn't declare |
| 007 US1, SC-007-04: a household that renews automatically, in the demo | `redeterminations_due` test set exists, but its path comes only from the rules engine | No named household for the demo, and the path ignores the reference lookup |
| FR-008-04: automatic renewal rate expected values | History seeds new applications only | No redetermination cases or outcomes, no expected automatic renewal rate |
| FR-008-03: procedural denial rate | Seed calculates missing-information denials ÷ **all decided cases** | Spec divides by **denials and coverage endings** |
| FR-004-13: seeded explanations in the 004a shape | `_explanation` in `history.py` writes one audience, citations as plain references | Shape differs from `DecisionExplanation` ([mvp-contracts.md](mvp-contracts.md) section 2) |

## Tasks

- [ ] **S-01** `[data]` Reference records. For every seeded member, write one
      `reference_records` document: `household_id`, `member_id`, `given_name`, `family_name`,
      `date_of_birth`, `jobs: [{employer, monthly_gross}]`. By default the reference income is
      the member's documented monthly income for the current program year (FR-003-18).
      Deliberate disagreements, picked by the seeded random draw and recorded as scenario tags:
      - `reference-identity-mismatch`: 3 households, date of birth off by one year
      - `reference-income-differs`: 10 households, one job differs by 15–30%
      - `reference-undeclared-job`: 3 households, one extra job
      - `reference-job-missing`: 2 households, a declared job has no reference income

      Demo households A, B and C keep exact matches, so the new-application demo is clean.
      Test: `test_FR_002_22_reference_records_cover_every_member` and one test per tag.
- [ ] **S-02** `[data]` Reference test set. Add `testsets/reference_lookup.json`: for each tagged
      household, the expected `ReferenceAnswer` and, for households due for renewal, the
      expected "missing or out of date" items under FR-007-13. 002 and 007 test against it.
- [ ] **S-03** `[data]` Migration `0006_mvp` creates the MVP collections and indexes
      ([mvp-contracts.md](mvp-contracts.md) section 5). `db/seeds/reset.py` clears and reloads
      `reference_records`.
- [ ] **S-04** `[data]` Demo renewal household E, "renewal-automatic" (no login needed):
      active coverage ending within the demo window, eligible, reference data agrees. A
      caseworker starts its redetermination and it renews automatically (007 US1). It is
      excluded from the random history plans, so its numbers stay fixed. (007b is dropped, so
      the second demo household and its `applicant4` login are not needed.) Update
      `redetermination_items` so `expected_path` also follows the FR-007-13 lookup, not just
      the rules engine.
- [ ] **S-05** `[data]` Seeded redetermination history and metrics. Add about 30 past
      redetermination cases (`case_type: redetermination`) across the two program years,
      linked to earlier coverage periods:
      - about 60% `renewed_automatically`
      - about 25% `renewed_after_response`
      - about 15% `ended_by_caseworker` with reason `missing_information`

      Each ends with a renewed coverage period, or an ended one, whose status matches. In
      `test_sets.py`:
      - add `automatic_renewal_rate` per month: renewed automatically ÷ redeterminations that
        ended that month (FR-008-08)
      - change `procedural_denial_rate` to: denials and coverage endings with reason
        `missing_information` ÷ all denials and coverage endings
      - keep `average_days_to_decision` and `share_decided_within_deadline` to new applications
        only, as the 008 metric definitions say

      Test: `test_FR_008_04_expected_metrics_match_hand_count` on a small fixture worked out
      by hand.
- [ ] **S-06** `[data]` Seeded explanations in the 004a shape. Once 004a's
      `explain_determination` is merged, `history.py` calls it for both audiences instead of
      `_explanation`, and writes `decision_explanations` documents. Until then, change only the
      shape (`audience`, `citations` as `Citation` objects) so the case page and applicant
      history render seeded and new explanations the same way.
- [ ] **S-07** `[data]` Regenerate the data set, commit the new manifest, and update
      `db/seeds/README` (or the data set section of 003's quickstart) with the new scenario
      tags and the two demo households.

Done when: `make seed` loads cleanly twice with identical hashes, the 003 tests still pass, and
002, 007 and 008 can each point a failing test at a named seeded household or test set.
