# Workflows lane: needs a change outside `apps/worker/`

## 1. Seeded `stub_result` can't be read by the worker (T010, research R1) — platform-ui / architect

The data lane stores `stub_result` on `households` (`db/seeds/generate.py`, migration 0002). `Scope.for_worker` refuses `households` (ADR-001-06), so `determine_eligibility` can't read it without bypassing the scope. For now `apps/worker/main.py` wires `FixedStubResults()`, which means every household is `eligible`. Tests inject the per-household results, so TC-15 covers the stub's behaviour.
**Needed:** either (a) `packages/platform/scope.py` lets a worker scope read `households` filtered to `_id = scope.household_id` (projection `stub_result` only), or (b) the data lane also exposes the stub results somewhere the worker may read. After that, the workflows lane adds a `MongoStubResults` reader (about 10 lines) in `apps/worker/activities/determination.py` and wires it in `main.py`.

## 2. `Determination` has no `failed_rules` (TC-37, FR-001-16) — contracts (003 owns the shape)

`packages/domain/case.Determination` has a single `reason_code`, so a determination can't say that both income and another rule failed. The precedence rule now sits in `apps/worker/workflows/case_states.denial_reason_for(reason, failed_rules)` (income first, as test-plan Findings recommend), and it is unit-tested with two failed rules. TC-37 at workflow level can only send the one code.
**Needed:** add `failed_rules: list[DenialReason] = []` to `Determination` in `packages/domain/case.py` (contracts step, BA-8). The workflow will then pass that list instead of `[reason_code]` (a one-line change in `case.py::_open_review`).

## 3. FYI, no action needed: a wake-up timer in the review wait (R3)

Temporal queries see `workflow.now()` as of the last workflow task. Without a wake-up, the `status` query's `days_remaining` would stay frozen during a long review wait (TC-44 failed this way). The wait now uses `wait_condition(timeout=until_next_case_day(clock))`, which wakes at each case-clock Chicago midnight and takes no action. R3 says "no timer", so the architect may want to note this in research.md.

## 4. FYI: checks outside this lane

- `tests/apps/worker/test_smoke_integration.py` (existing) needs the Temporal dev server on :7233. It wasn't running, so it fails here.
- `tests/apps/worker/test_interceptors.py` (existing, unchanged) has 8 mypy errors.
- `tests/apps/worker/repositories/test_cases.py` sets `pytestmark = pytest.mark.integration`, because by path `tests/conftest.py::level_for` would mark it `unit`. It needs the replica-set MongoDB.
