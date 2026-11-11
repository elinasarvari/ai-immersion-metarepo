# ADR-003-07: Merging main (001 case lifecycle, 010 review queue) into the 003 branch

- **Status:** Accepted – auto-decided
- **Decided by:** integrator (automated), 2026-11-10
- **Revisit if:** T023 replaces the stub determination activity (then T011 drops `stub_result` and `household_stub_results` as ADR-003-04 plans), or the data lane wants a different household as demo household C
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-06, FR-003-10, FR-003-14, FR-003-19; main's FR-001-16, FR-001-24
- **Lanes affected:** Knowledge & data
- **Repos affected:** benefit-be
- **Supersedes:** – (carries out the merge step ADR-003-04 asks for; ADR-003-04 stays Accepted)

## Context

`origin/main` moved 9 commits (PR #2 `feature/001-case-lifecycle`, PR #3 `feature/010-review-queue`) while 003 was being built. Git reported conflicts in `db/seeds/generate.py`, `tests/db/seeds/test_reset.py` and `tests/db/test_migrations.py`; the semantic clashes are the migration order and the demo households.

## Options

### Option A: 003 adapts to main, keeping main's stubs working until 003 replaces them
Renumber 003's migration after main's, build its `households` validator on main's 0003, make main's demo households A/B/C three of 003's 200 generated households, and keep 001's stub fields until T023/T011.
- **Pros:** main's behaviour (001 stubs, applicant1–3 paths in `make dev`) keeps working; FR-003-10's 200 households hold; no edit to applied migrations (KD-11).
- **Cons:** `stub_result` lives on three 003 households for a while.

### Option B: Drop main's stubs in the merge
- **Cons:** breaks main's determination stub and its tests before 003's activity (T023) exists; does lane work inside a merge.

## Comparison

| Criterion | A | B |
|---|---|---|
| Meets both specs | yes | breaks FR-001-16 until T023 |
| Constitution and rules (VI, KD-11) | yes | yes |
| Simplicity (X) | high | low |
| Reversibility | high | medium |

## Decision

We choose **Option A**. Main wins on every shared definition; 003 keeps its requirements.

| # | Clash | Main has | Feature had | Kept, and why |
|---|---|---|---|---|
| 1 | Migration number | `0002_review_queue`, `0003_case_lifecycle`, `0004_case_screens` | `0002_eligibility` (sorted before 0003, whose `households` validator would then erase `address_state`/`seed_key`) | Renamed to `0005_eligibility.py` (and its test to `tests/db/migrations/test_0005_eligibility.py`); runs after main's (ADR-003-04, KD-11) |
| 2 | `households` validator | 0003: baseline + `stub_result` | 0002: baseline + `address_state`, `seed_key`; downgrade to baseline | 0005 = main's 0003 schema + `address_state`, `seed_key`; downgrade restores 0003's schema, not the baseline. `stub_result` is dropped later by T011 |
| 3 | Seeded households | 3 households A/B/C with `stub_result` + `household_stub_results` | 200 generated households with A, B; no C | 200 households (FR-003-10); `db/seeds/households.py` gives the "missing-document" named household main's ID `HOUSEHOLD_C` (`household-c`, cannot-determine, matching its stub result); `household_documents(dataset)` adds `stub_result` to A/B/C; `household_stub_results` still seeded |
| 4 | Seed run | applications for seeded cases | members, rule sets, `_meta.anchor_date` | Both: generate.py writes households, stub results, members, rule sets, applications, users, `_meta` with `anchor_date` |
| 5 | `test_reset.py` | `ids == {A, B, C}`; stub docs have exactly `{_id, created_at, stub_result}`; reseed test clears households, stub results, users, applications | `len(ids) == 200`, `{A, B} <= ids`; meta and rule-set tests | 200 households with `{A, B, C} <= ids`; the stub test filters the stub-bearing docs and allows 003's two fields; the reseed test also clears `household_members` (they would otherwise collide); 003's meta and rule-set tests kept |
| 6 | `test_migrations.py` version lists | 0001–0004 | 0001, 0002_eligibility | Main's tests, each list extended with `0005_eligibility` (applied order, and down/up lists that pass through it) |

## Consequences

- **Good:** both features' requirements hold on the merged branch; main's demo paths still run.
- **Bad / accepted trade-offs:** `stub_result` and `household_stub_results` stay until T023/T011; household C's seed key changes from `household-missing-document` to `household-c`, so its member, job and document IDs differ from the pre-merge branch (no test or known answer referenced them).
- **Work this creates:** none new; T002 (one `Relationship`/`PayFrequency`), T011 (relationship enum = main's 8, drop stub fields, new collections), T023 and T025 still do the rest of ADR-003-04.

## How we verify it

`make check` steps, and `tests/db/test_migrations.py` / `tests/db/seeds/test_reset.py` in the integration run (CI, verify loop).

## References

ADR-003-04, ADR-001-06; benefit-be merge commit `08199ed`; main `db/migrations/versions/0003_case_lifecycle.py`, `db/seeds/generate.py`, `db/seeds/users.py`.
