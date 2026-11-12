# Implementation Plan: Eligibility Rules and Synthetic Data

**Branch**: `feature/003-eligibility-rules` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-eligibility-rules/spec.md`

**Target repos**: `repos/benefit-be` (engine, data set, worker activity, API) and `repos/benefit-fe` (case page determination section).

## Summary

A pure `evaluate(household_snapshot, as_of_date)` engine (six rules ELIG-01…06, effective-dated 2025/2026 rule sets) replaces 001's determination stub inside the existing `determine_eligibility` activity, which captures the case's snapshot once, stores the full determination and returns 001's summary unchanged. A fixed-seed generator produces 200 households, pay stubs, test sets for 002/003/007/008 and completed history. Caseworkers see each determination's per-rule trace on the case page through a new read endpoint.

The branch already contains the engine, models, a migration and most of the generator (research R0). Remaining work: align with main (001 and 010 landed), snapshot capture and the activity, the interim verifications, the missing test sets and history, the API and the UI section.

## Technical Context

**Language/Version**: Python 3.12 (`repos/benefit-be/.python-version`); TypeScript strict, React (benefit-fe)
**Primary Dependencies**: Pydantic v2, FastAPI, temporalio, PyMongo async, reportlab (stub PDFs), hypothesis (property tests, R9); benefit-fe: TanStack Query, shadcn/ui, generated OpenAPI client. No new dependency.
**Storage**: MongoDB 8.0 single-node replica set (000 R27, draft constitution 2.0.0); collections per [data-model.md](data-model.md); migration `0005_eligibility`
**Testing**: pytest (unit, property, contract, integration with local MongoDB + Temporal, workflow replay); Vitest + Testing Library; Playwright e2e with axe
**Target Platform**: native macOS (PR-5); CI on GitHub-hosted runners
**Project Type**: web service + SPA (two repos)
**Performance Goals**: `evaluate` < 5 ms per household (unverified target; 200-household known-answer run < 1 s); seed generation < 60 s
**Constraints**: deterministic and pure engine (I, KD-1); identical seed output (SC-003-03); no names in traces or logs (VIII)
**Scale/Scope**: 200 households × 2 years, ≥30 known-answer cases, 10–20 extraction test stubs

## Constitution Check

Written against the draft 2.0.0 text (MongoDB only), as 000's plan is (000 R27); if the amendment is refused, only the storage tasks change.

| Principle | Result |
|---|---|
| I. AI assists, rules decide | Pass. Outcome comes only from `packages/rules.evaluate`; the stub's fixed outcomes are removed (ADR-003-02, ADR-003-03). |
| II. Durable, deterministic orchestration | Pass. No workflow code change; the activity is idempotent by deterministic IDs (ADR-003-02, R6). |
| III. Evidence for AI output | N/A (no AI). Policy refs on every rule result feed 004's citations. |
| IV. Human control | Pass. Ineligible and Cannot determine still go to 001/010 review; nothing here approves. |
| V. Test-first | Pass. Every FR-003-xx gets a named test (test plan by quality engineer); property tests per rule (KD-3). |
| VI. Contracts first | Pass. Domain models and OpenAPI in the `[contracts]` tasks first; reuse of main's models (ADR-003-04). |
| VII. Clear boundaries | Pass. Only `apps/worker/activities/` imports `packages/rules` (BA-4); API reads stored records. |
| VIII. Security, synthetic data | Pass. All seeds marked synthetic, member IDs only in traces, household scope on new collection (ADR-003-03), role-guarded endpoint (ADR-003-05). |
| IX. Production habits | Pass. Verifications behind a port with an interim implementation (ADR-003-03). |
| X. Simplicity | Pass. No new dependency, service or process. One temporary collection, stated in ADR-003-03. |

Post-design re-check: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/003-eligibility-rules/
├── plan.md  research.md  data-model.md  quickstart.md  scope.json
├── contracts/rules-interface.md  contracts/rest-api.openapi.yaml
├── decisions/README.md  decisions/ADR-003-01…06
└── tasks.md  test-plan.md   (later steps)
```

### Source Code

Layout per `project-rules/backend-architecture.md`. `+` new, `~` changed, `-` removed.

```text
repos/benefit-be/
  packages/domain/                    [contracts]
    ~ eligibility.py                  drop EligibilityResult, add DeterminationView
    ~ household.py                    reuse case.Relationship/PayFrequency; +as_of_date; +VerifiedMemberFacts
  packages/rules/                     [data]   engine as built; ~ stub.py imports POLICY_REFS
  db/migrations/versions/             [data]
    ~ 0005_eligibility.py             renamed from 0002 by the merge (ADR-003-07); T011 finishes it
  db/seeds/                           [data]
    ~ generate.py, ~ households.py    merged with main's, A/B/C demo households (ADR-003-07)
    ~ users.py link (FR-003-14)
    + verifications.py, + test_sets.py (002/007/008 sets), + history.py (ADR-003-06)
  apps/worker/                        [workflows]
    ~ activities/determination.py     real body (ADR-003-02)
    + activities/snapshot.py          build snapshot from members / form + VerifiedFacts
    + repositories/snapshots.py, determinations.py, verified_facts.py
    - repositories/stub_results.py    ~ main.py wiring
  packages/platform/scope.py          [platform-ui]  + seeded_verifications, - household_stub_results
  apps/api/                           [platform-ui]
    ~ routers/cases.py  + services/determinations.py  + repositories/determinations.py  + schemas/determinations.py
  openapi/openapi.json                [platform-ui]  regenerated
  tests/                              mirrors the above

repos/benefit-fe/                     [platform-ui]
  openapi/openapi.json, src/api/generated/schema.d.ts   regenerated
  + src/api/determinations.ts (+ test)
  + src/features/caseworker/case-page/DeterminationSection.tsx (+ test)
  ~ src/features/caseworker/case-page/sections.tsx
  + e2e/caseworker-sees-determination.spec.ts; ~ e2e comments that mention stub results
```

**Structure Decision**: the existing two-repo layout; no new top-level folder (BA-1).

## Architecture decisions

| ADR | Decision | Status |
|---|---|---|
| ADR-003-01 | Rule sets as versioned code; seeded copy in `rule_sets` | Accepted |
| ADR-003-02 | Activity stores the full determination; workflow keeps 001's summary | Accepted |
| ADR-003-03 | Snapshot capture in the worker; `seeded_verifications` until 002/005 | Accepted |
| ADR-003-04 | Reuse main's definitions; migration renumbered to `0005_eligibility` | Accepted |
| ADR-003-05 | `GET /api/v1/cases/{case_id}/determinations` + `DeterminationSection` | Accepted |
| ADR-003-06 | Completed-history seeding scope | **Needs decision** — plan assumes Option A |
| ADR-003-07 | Merge of main (001, 010): 0005 on main's 0003 `households`; A/B/C among the 200 | Accepted – auto-decided |

### Open questions
- ADR-003-06: seed only stores that exist on main, hand explanations and other notice types to 004/011 as generated files, no history on demo households. Recommendation: Option A.

## Contracts between lanes

| Contract | Provider → consumer | Where |
|---|---|---|
| `evaluate(HouseholdSnapshot, date) -> Determination` | data → workflows | [contracts/rules-interface.md](contracts/rules-interface.md) |
| `determine_eligibility` activity (unchanged signature) | workflows → 001 workflow | same |
| `VerifiedFacts` port + `VerifiedMemberFacts` | data (interim) → workflows; replaced by 002/005 | same, [data-model.md](data-model.md) |
| `HouseholdSnapshot`, `DeterminationRecord` in `determinations` | data → 004, 007, 008, API | [data-model.md](data-model.md) |
| `listCaseDeterminations` / `DeterminationView` | platform-ui (be) → benefit-fe | [contracts/rest-api.openapi.yaml](contracts/rest-api.openapi.yaml) |
| Generated test sets | data → 002, 007, 008, evals | data-model.md "Generated test sets" |

Order: merge `origin/main` → `[contracts]` (domain + OpenAPI) → data, workflows, platform-ui in parallel → e2e. The benefit-be PR opens before benefit-fe (PL-3).

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| Temporary `seeded_verifications` collection | Demo outcomes from real rules before 002/005 (ADR-003-03) | Form-only snapshots make every demo case Cannot determine |
