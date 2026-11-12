# Research: 003 Eligibility rules and synthetic data

Date of every entry: 2026-11-10. Sources are cited as `repo@ref:path:line`. `branch` = `feature/003-eligibility-rules` (b107708), `main` = `origin/main` (benefit-be 427f598, benefit-fe 0af1e5b).

## R0. Starting point

- `benefit-be@branch` already carries a first cut of 003 (commit b14bf98): the engine (`packages/rules/engine.py`, `checks.py`, `income.py`, `rule_sets.py`, `stub.py`), the domain models (`packages/domain/eligibility.py`, `household.py`), migration `0002_eligibility`, the 200-household generator (`db/seeds/households.py`, `documents.py`) and `db/seeds/data/known_answers.json`. One test is xfailed for the missing test sets (`tests/integration/test_seeded_dataset.py:43`).
- The branch forks from benefit-be main 3270bbb. Since then main has gained 010 (review queue, migration `0002_review_queue`) and 001 (case lifecycle, migrations `0003_case_lifecycle`, `0004_case_screens`, the determination stub `apps/worker/activities/determination.py`). The plan keeps what the branch built and closes the gaps; ADR-003-04 settles the clashes with main.
- No earlier plan or ADR for 003 exists in the metarepo (`git log --all -- specs/003-eligibility-rules/plan.md` is empty), although `packages/rules/rule_sets.py:1` cites "ADR-003-01". ADR-003-01 here records that decision.

## R1. Rule IDs and policy references
- **Decision:** keep `ELIG-01`…`ELIG-06` in FR-003-01 order, policy refs `TM-2.1`…`TM-2.5`, `TM-3.1` (`packages/rules/rule_sets.py:19`). 004 writes the training manual so that these section IDs exist; until then they are placeholders the known-answer tests pin.
- **Reason:** stable IDs already stored in the snapshot contract test (`tests/contract/snapshots/eligibility_models.json`).
- **Alternatives:** descriptive IDs (`residency`, …): rejected, they churn when wording changes.

## R2. Money and rounding
- **Decision:** `Decimal` everywhere; monthly income per stub rounded half-up to the cent (FR-003-18); monthly limit `floor(annual × 1.38 ÷ 12)` to the whole dollar (FR-003-15: 1 person, 2026 → $1,782). Stored as strings in MongoDB (`0002_eligibility.py:18`).
- **Reason:** exact, reproducible across machines (FR-003-04); BSON Decimal128 would also work but the branch already stores strings and tests them.
- **Alternatives:** floats (non-reproducible); Decimal128 (no gain, migration churn).

## R3. Age
- **Decision:** whole years on the as-of date; a 29 February birthday counts on 1 March in non-leap years (`checks.py:20`).
- **Reason:** edge case "turns 19 or 65 within the coverage period" is decided on the as-of date only.

## R4. Result precedence
- **Decision:** as built (`engine.py:55`): no rule set → Cannot determine (`rule_set` missing, reason "no rules for date"); any fail → Ineligible (missing items still listed); any missing → Cannot determine; else Eligible. FR-003-20.

## R5. Mapping to 001's case outcome
- **Decision:** the activity maps the engine result to 001's `packages/domain/case.Determination` (main `packages/domain/case.py`, class `Determination`): `outcome` = same value; `failed_rules` = distinct `DenialReason`s in rule order, `ELIG-06` → `income_over_limit`, `ELIG-01`…`05` → `other_rule_not_met`; `reason_code` = `income_over_limit` if ELIG-06 failed, else `other_rule_not_met` if any rule failed, else `None`; `missing_items` = the merged `MissingItem.item` codes (deduplicated, in order). Cannot determine keeps `reason_code=None`, as the 001 stub does (main `apps/worker/activities/determination.py`, `stub_determination`).
- **Reason:** income is the reason the demo and notices talk about; the full per-rule detail stays in the stored record (ADR-003-02).
- **Alternatives:** first failed rule in ID order (would make residency outrank income, which the denial notice wouldn't explain well).

## R6. Deterministic IDs
- **Decision:** `determination_id = uuid5(case_id, "determination:<as_of>")` (same formula as the 001 stub, so stored references survive the switch); `snapshot_id = uuid5(case_id, "snapshot:<as_of>")`; history and test-set IDs from `db/seeds/ids.seeded_id`.
- **Reason:** idempotent activities (TW-11) and identical seeds (FR-003-10, SC-003-03).

## R7. Program year of seeded members
- **Decision:** `household_members` holds one document per member per coverage year (`coverage_year`, index `household_year`, `0002_eligibility.py:212`). The snapshot reads the members of the as-of date's calendar year (FR-003-21); "household size changes between years" falls out of this.

## R8. Attested facts from the application form
- **Decision:** for a household with no seeded members, the snapshot is built from 001's stored form (main `packages/domain/case.py`, `ApplicationForm`): `address.state` → `address_state`; `citizenship_status` `us_citizen`/`qualifying_immigrant` → `citizenship_attested=True`, `neither` → `False`; `medicare_entitled` as is; `zero_income` → `declared_zero_income`; each form job becomes a job with `job_id = uuid5(case_id, "job:<member index>:<job index>")` and no stubs until 002 provides them; `identity_verified=None` until 005 provides it.
- **Reason:** FR-003-16; missing evidence yields Cannot determine, never Ineligible (FR-003-03).

## R9. Hypothesis
- **Decision:** property tests per rule with `hypothesis` (KD-3); check that it is already a pinned dev dependency in `uv.lock` before adding it (unverified; PR-4).

## R10. Pay stub rendering
- **Decision:** keep `reportlab` PDFs and PNGs with a visible "SYNTHETIC" marker via `packages.platform.synthetic.stamp_pdf` (`db/seeds/generate.py:28`); poor-quality stubs are PNGs with noise and skew from a seeded RNG (`documents.py:42`). Byte-identical output is checked by the existing `tests/db/seeds/test_generated_documents.py`.
- **Alternatives:** Pillow-only images (no text layer for 002's extraction tests).

## R11. Determination read audit
- **Decision:** reading determinations writes an audit entry the same way `get_case_detail` does (main `apps/api/routers/cases.py`, `get_case`, which takes an `AuditWriter`). Inputs in traces carry member IDs only, never names (`checks.py:4`).

## R12. Frontend data
- **Decision:** a separate query `useCaseDeterminations(caseId)` with key `['cases', caseId, 'determinations']` (FE-4, FE-5), generated client types from the regenerated `openapi/openapi.json` (FE-3); the section registers in `caseSections` only (main `src/features/caseworker/case-page/sections.tsx`, "a later feature adds its section here and nowhere else").
