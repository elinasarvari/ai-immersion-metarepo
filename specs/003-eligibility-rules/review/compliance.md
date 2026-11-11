# Compliance review: 003-eligibility-rules

**Verdict: PASS**: 0 critical, 0 major, 1 minor. Full review (no earlier snapshot). Scope: benefit-be (`origin/main...HEAD` plus the working tree, 67 uncommitted) and benefit-fe (14 uncommitted).

| # | Severity | File:line | Rule/ADR/TC | Violation | Required change |
|---|---|---|---|---|---|
| 1 | minor | benefit-be:tests/apps/worker/workflows/test_determination_failures.py:38 | TC-99, TW-10 | The plan says TC-99 uses a store that "always raises" and expects the case to end `under_review`. The test fails the store 5 times, then lets it recover. `under_review` then comes from the ELIG-01 ineligible result (`adverse_determination`), not from failure handling. The test does prove what ADR-001-02 (UNTIL_DONE) allows: retries past RULES_STEP's 3 attempts, one stored record, and the case not stuck in `determining`. But it doesn't prove the case as the plan words it. | Update TC-99's wording in test-plan.md to match ADR-001-02 (the outage outlasts the step's attempts, then recovers, and the case isn't left `determining`). The other option is a test that matches the current wording. |

## Checked and compliant
- **KD-1 / FR-003-08 (rules are pure):** `packages/rules` imports only the standard library and `packages.domain`. It doesn't read the clock, and `evaluate(snapshot, as_of_date)` is the entry point.
- **BA-3/4/5/6/7, PL-2 (import boundaries):** `packages.rules` is imported only by `apps/worker/activities/determination.py`, plus seeds (allowed by BA-10). No imports between `apps/api` and `apps/worker`. `packages/domain` imports only `packages.domain`.
- **ADR-003-01:** rule sets live in code. `stub.py` uses `POLICY_REFS`, so the duplicate is gone. TC-65 compares the seeded docs with `RULE_SETS`.
- **ADR-003-02:** no file under `apps/worker/workflows/` changed. The activity keeps its name and types. `determination_id` uses the stub's formula. A duplicate-key insert counts as done (TW-11).
- **ADR-003-03:** one snapshot per `(case_id, as_of_date)`, reused once stored. `stub_results.py` and `FixedStubResults` are removed. `seeded_verifications` is in `SCOPED_HOUSEHOLD_ONLY`. TC-102 proves the worker can't read another household's rows.
- **ADR-003-04/07:** one `PayFrequency` and `Relationship` (from `case.py`), and no `EligibilityResult`. Only `0005_eligibility.py` is new under `db/migrations/versions`; no applied migration is edited (KD-11). The migration has a downgrade.
- **ADR-003-05, PL-1/6/7:** `GET /api/v1/cases/{case_id}/determinations` uses `require_roles(caseworker)`, a scoped repository read (projection, `limit 20`) and an audited read. TC-105 to TC-107 cover the 403 and 401 responses and the audited applicant refusal. The OpenAPI file is regenerated, and the FE client too (FE-3).
- **Database rules:** every repository query goes through `packages.platform.scope` (household filter), with typed filters and projections. Validators set `additionalProperties: false`, and money is stored as decimal strings.
- **PR-3 / KD-13 (synthetic data):** names are made-up committed lists with no Faker, and employers are obviously fictional. Seeds use `random.Random(f"{SEED}:{stream}")`. No SSN patterns. Validators accept `synthetic: true`, and TC-85 checks it on every seeded collection.
- **Security:** the committed broad `.gitleaks.toml` allowlist of `known_answers.json` is reverted in the index. The new `scripts/gitleaks.toml` allowlists only `case_key` matches of `generic-api-key` in that file. `make check`, CI and `verify.py` all use it.
- **Frontend:** FE-4 (TanStack hook in `src/api/`), FE-5 (query key includes the case ID) and FE-10 (loading, error with retry, and empty states) are met. TC-127 runs an axe check.
- **Test plan:** the tests I sampled prove their cases: TC-95, TC-96, TC-102 and TC-124 to TC-128, which compare the UI rows with `GET …/determinations`.

## Notes (ambiguous for this case)
- **TW-9 vs ADR-003-03:** `apps/worker/activities/snapshot.py` holds the form-to-facts mapping and the merge of verified facts. It is a helper class rather than an activity, and ADR-003-03 places snapshot capture inside `determine_eligibility`. Please clarify whether this mapping counts as "business logic" under TW-9, or whether it belongs in a package (for example `packages/domain` helpers) when 002 and 005 land.
- **PR-6:** `benefit-be:check` and `benefit-fe:check` pass (verify.md). The e2e run didn't happen locally because the ports were in use; CI runs it.
