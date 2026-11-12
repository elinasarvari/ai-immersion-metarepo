# ADR-003-01: Rule sets are versioned code; the database holds a seeded copy

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-06, FR-003-07, FR-003-08, FR-003-15, FR-003-21
- **Lanes affected:** Knowledge & data
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

Income limits and rule parameters must be versioned by effective date, with 2025 and 2026 loaded (FR-003-06, FR-003-15), and evaluation must depend on nothing but its inputs (FR-003-08, KD-1: no I/O). The branch already holds both years as frozen `RuleSet` objects in `benefit-be@branch:packages/rules/rule_sets.py:47` and seeds a copy into `rule_sets` (`db/seeds/rule_sets.py`, validator in `db/migrations/versions/0002_eligibility.py:154`). Its docstring cites "ADR-003-01", which was never written; this ADR records it.

## Options

### Option A: Rule sets as code in `packages/rules`, seeded copy in `rule_sets` for reading
`rule_set_for(as_of_date)` picks from a tuple of frozen models; a published `(rule_set_id, version)` never changes, a change is a new version. The seed writes the same objects to `rule_sets` so the API, 004 and 008 can show limits without importing `packages/rules` (BA-4).
- **Pros:** pure and reproducible; reviewed in a PR like any rule change; no I/O in the engine.
- **Cons:** two copies; a test must prove they match.

### Option B: Rule sets loaded from `rule_sets` and passed into `evaluate`
The activity reads the rule set and passes it in.
- **Pros:** one source; limits change without a deploy.
- **Cons:** changes the agreed signature `evaluate(household, as_of_date)` (specs/README.md, KD-1); a database edit could change past determinations, breaking replay (US3).

### Option C: Configuration files (YAML) read at import
- **Cons:** file I/O at import in a "pure" package; no gain over code for two years.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-003-06/07/08) | yes | yes | yes |
| Constitution and rules (I, KD-1) | yes | changes the agreed interface | weak (import I/O) |
| Simplicity (X) | high | medium | medium |
| Security and privacy | n/a | n/a | n/a |
| Testability | high | medium | medium |
| Fits existing code and ADRs | already built | rewrite | rewrite |
| Reversibility | high | medium | high |
| Effort | none | medium | low |

## Decision

We choose **Option A** because it keeps `evaluate` pure with the agreed signature, makes past determinations replayable from code history, and is already built and tested. FR-003-15's "versioned configuration" is met by effective-dated, never-edited versions in code.

## Consequences

- **Good:** replay of any past date is exact; known-answer cases pin both years.
- **Bad / accepted trade-offs:** a limit change needs a PR and deploy (acceptable: limits are fixed project values, specs/README.md).
- **Work this creates:** [data] keep `rule_sets.py`; add a test that the seeded `rule_sets` documents equal `RULE_SETS`; [data] remove the duplicate `_POLICY_REFS` in `packages/rules/stub.py:15` (import `POLICY_REFS`).

## How we verify it

CI: `tests/contract/test_rules_purity.py` (no I/O imports in `packages/rules`); a seed test comparing `rule_sets` documents to `RULE_SETS`; known-answer tests for both years (FR-003-09). Compliance review checks no edit to a published version.

## References

KD-1, KD-2, BA-4, constitution I and X, specs/README.md "Interfaces between lanes" and "Project values".
