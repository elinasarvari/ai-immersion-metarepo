# ADR-003-02: The activity stores the full determination; the workflow keeps 001's summary

- **Status:** Accepted
- **Date:** 2026-11-10
- **Feature:** specs/003-eligibility-rules/ · **Requirements:** FR-003-02, FR-003-04, FR-003-05, FR-003-19, FR-003-23
- **Lanes affected:** Knowledge & data, Workflows, Platform & UI
- **Repos affected:** benefit-be
- **Supersedes:** –

## Context

On main, `CaseWorkflow` calls the activity `determine_eligibility(DeterminationRequest) -> Determination` (`benefit-be@main:apps/worker/activities/determination.py`), where `Determination` is 001's minimal model ("003 owns the full shape. 001 never changes it", `packages/domain/case.py`, class `Determination`). The activity is a stub and its docstring says "003 replaces the body with its rules (TW-9)". The engine on the branch returns a richer `packages/domain/eligibility.Determination` with per-rule results (`benefit-be@branch:packages/domain/eligibility.py:76`). The case page needs the full trace (FR-003-23); workflow histories should stay small and running workflows must not break (TW-7, TW-14 replay tests `tests/apps/worker/histories/case_*.json`).

## Options

### Option A: Replace the stub body; persist the full record; return 001's summary
`determine_eligibility` captures the snapshot (ADR-003-03), calls `evaluate`, inserts a `DeterminationRecord` into `determinations` (`_id = determination_id`, idempotent on duplicate key), and returns `case.Determination` mapped per research R5. Activity name, input and output types are unchanged.
- **Pros:** no workflow change, replay histories stay valid; small history payloads; the API reads the stored record.
- **Cons:** two determination models (summary and full), with a mapping to test.

### Option B: Return the full engine determination to the workflow
Change the activity output to `eligibility.Determination`; the workflow stores it.
- **Pros:** one model.
- **Cons:** changes a contract on main used by 001 and 010 (BA-8, constitution VI), needs `workflow.patched()` (TW-7), bigger histories, and the workflow lane must change its persistence.

### Option C: Separate `record_determination` activity called by the workflow
- **Cons:** a workflow change for no gain; two activities to keep idempotent together.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec | yes | yes | yes |
| Constitution and rules (VI, BA-8, TW-7, TW-11) | yes | contract change on main | workflow change |
| Simplicity (X) | high | low | medium |
| Security and privacy | traces keep member IDs only | same | same |
| Testability | activity test + mapping test | replay re-recording | more tests |
| Fits existing code and ADRs | matches the stub's stated plan | against "001 never changes it" | partial |
| Reversibility | high | low | medium |
| Effort | low | high | medium |

## Decision

We choose **Option A**: it is the replacement the 001 stub was designed for, keeps every contract on main, and makes the stored record the single source for the case page. `determination_id` keeps the stub's formula (research R6) so `CaseOverride.determination_id` references stay valid.

## Consequences

- **Good:** 001/010 workflows and their replay histories are untouched.
- **Bad / accepted trade-offs:** the summary loses per-rule detail; consumers needing it read `determinations`.
- **Work this creates:** [contracts] `DeterminationRecord` gains `as_of_date`-keyed deterministic `_id`, keep in `packages/domain/eligibility.py`; [workflows] replace the body of `apps/worker/activities/determination.py`, add `apps/worker/repositories/determinations.py` (insert via `packages.platform.scope.insert_one` under `Scope.for_worker`), the mapping function with tests; [data] engine unchanged.

## How we verify it

Activity unit test: same request twice → one stored record, identical summary (FR-003-04, TW-11). Mapping test per outcome. The existing replay tests `test_case_replay.py`, `test_review_replay.py` pass unchanged (CI). Code reviewer checks no workflow file changed for this.

## References

TW-7, TW-9, TW-11, TW-14, BA-4, BA-8, KD-2, constitution I, II, VI; main `packages/domain/case.py`, `apps/worker/activities/determination.py`.
