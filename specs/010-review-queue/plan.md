# Implementation Plan: Review Queue and Caseworker Actions

**Branch**: `feature/010-review-queue` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-review-queue/spec.md`

**Target repo**: `repos/benefit-be` only. No frontend change: the queue screens and the REST endpoint that sends actions are 006 (spec "Out of scope").

## Summary

Give every review reason its exact actions (FR-010-01), refuse and record anything else (FR-010-05), apply each action once (FR-010-06), flag tasks for reminder and escalation on the case clock (FR-010-02), send verification and determination failures to a person (FR-010-03), and allow one automatic request for information per case (FR-010-04). `CaseWorkflow` owns each task as a durable wait and writes a MongoDB projection for the shared queue (ADR-010-01); actions arrive as one signal validated against a shared action table (ADR-010-02); reminders and escalation are per-task Temporal timers (ADR-010-03); retry limits come from activity retry policies (ADR-010-04).

## Technical Context

**Language/Version**: Python 3.12 (`benefit-be:.python-version`; 000 research.md)

**Primary Dependencies**: Temporal Python SDK (`temporalio`), Pydantic v2, PyMongo async, structlog. No new dependency (constitution X).

**Storage**: MongoDB 8.0 single-node replica set; collections `review_tasks`, `caseworker_actions`, `case_events`, `eval_overrides`, `audit_log` (baseline `0001`), tightened by migration `0002_review_queue`.

**Testing**: pytest with markers `unit`, `workflow` (time-skipping, replay, restart), `integration` (`benefit-be:pyproject.toml:61-66`); names `test_FR_010_<nn>_…` (testing.md).

**Target Platform**: macOS native processes via `honcho` (PR-5, PL-12).

**Project Type**: backend service (Temporal worker + MongoDB).

**Performance Goals**: none beyond the spec; queue reads are single indexed queries (database.md).

**Constraints**: workflow determinism (TW-1); every side effect an idempotent activity (TW-2, TW-11); waits configurable and on the demo time scale (FR-011-04); no personal data in history or logs (VIII, PL-11).

**Scale/Scope**: six reasons, eleven action types, synthetic demo volumes.

## Constitution Check

| Principle | Result |
|---|---|
| I. AI assists, rules decide | Pass: overrides are human actions; stored determination never changed (research R7, FR-001-20). |
| II. Durable, deterministic orchestration | Pass: ADR-010-01, ADR-010-02 (idempotent actions), ADR-010-03 (timers). |
| III. Evidence for every AI output | Pass: "missing citation" routes to Verification review; evidence by reference (R3). |
| IV. Human control | Pass: adverse and AI-drafted notices need an action; overrides recorded and fed to evals (R6). |
| V. Test-first | Pass: every FR-010 has named workflow/integration tests (ADR "How we verify it"); test plan by the quality engineer. |
| VI. Contracts first | Pass: `packages/domain/review.py` and `contracts/workflow-review.md` go in the contracts PR; 001/002/003/004/007/011 stubbed. |
| VII. Clear boundaries | Pass: workflows import no DB code (TW-2); worker repositories only in activities (R4); BA-3 to BA-7 kept. |
| VIII. Security and synthetic data | Pass: household filter in worker repositories (R4); free-text reasons never logged. |
| IX. Production habits | Pass: waits from settings; activities have presets with timeouts (TW-10). |
| X. Simplicity | Pass: no new process, store or dependency. |

## Project Structure

### Documentation (this feature)

```text
specs/010-review-queue/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/workflow-review.md
├── decisions/ (README.md, ADR-010-01 … ADR-010-06)
└── scope.json
```

### Source Code (`repos/benefit-be`, layout per backend-architecture.md)

```text
packages/domain/review.py                 [contracts] enums, ALLOWED_ACTIONS, models
apps/worker/workflows/review.py           [workflows] open_review, action processing, open_tasks
apps/worker/workflows/review_timers.py    [workflows] pure due-time functions (ADR-010-03/06)
apps/worker/workflows/case.py             [workflows] CaseWorkflow hooks (owned by 001; 010 adds the review loop)
apps/worker/activities/review_tasks.py    [workflows] upsert/flag/close/record activities (thin, TW-9)
apps/worker/repositories/review_tasks.py  [workflows] MongoDB access, household-scoped (R4)
apps/worker/repositories/caseworker_actions.py
apps/worker/policies.py                   [workflows] RULES_STEP preset (ADR-010-04)
db/migrations/versions/0002_review_queue.py  [data] validators and indexes
tests/apps/worker/workflows/test_review*.py, test_review_replay.py, histories/review_v1.json
tests/apps/worker/activities/test_review_tasks.py
tests/db/migrations/test_0002_review_queue.py
```

**Structure Decision**: existing `benefit-be` layout; the only new folder is `apps/worker/repositories/`, inside the lane's own folder and anticipated by database.md (R4). Settings `REVIEW_REMINDER_DAYS`, `REVIEW_ESCALATION_DAYS` are added to `packages/platform/settings.py` and `.env.example` by Platform & UI as a contracts item.

## Architecture decisions

| ADR | Decision | Status |
|---|---|---|
| ADR-010-01 | CaseWorkflow owns tasks; `review_tasks` is a projection | Accepted |
| ADR-010-02 | One `caseworker_action` signal with `action_id`; shared action table; workflow authoritative | Accepted |
| ADR-010-03 | Per-task Temporal timers on the case clock for reminder and escalation | Accepted |
| ADR-010-04 | Retry limit from RetryPolicy (3 attempts); terminal failure opens review | Accepted |
| ADR-010-05 | Reason for a failed determination | Accepted (A: "Cannot determine", cause `determination_failed`) |
| ADR-010-06 | How review days are counted | Accepted (A: elapsed case-clock time) |

## Contracts between lanes

| Contract | Provider | Consumers | Where |
|---|---|---|---|
| `ReviewReason`, `ActionType`, `ALLOWED_ACTIONS`, `REASON_REQUIRED`, `ReviewTask`, `CaseworkerActionSignal`, `CaseworkerAction` | contracts PR (all lanes) | Workflows, Platform & UI (006), Knowledge & data (008) | `packages/domain/review.py`, data-model.md |
| `caseworker_action` signal, `open_review_tasks` query | Workflows | Platform & UI (006 API) | contracts/workflow-review.md |
| `open_review(...)` helper | Workflows (010) | Workflows (001, 007, 011) | contracts/workflow-review.md |
| `review_tasks` / `caseworker_actions` schema and indexes | Knowledge & data (migration `0002`) | Workflows (writes), Platform & UI and 008 (reads) | data-model.md |
| Settings `REVIEW_REMINDER_DAYS`, `REVIEW_ESCALATION_DAYS` | Platform & UI | Workflows | data-model.md, ADR-010-03 |
| Used, stubbed until ready: `CaseWorkflow` and states (001), case clock and advance-clock (011), `verify_documents`/`draft_request` (002), `evaluate` (003), explanation checks (004), coverage end (007) | other features | Workflows (010) | specs/README.md "Interfaces between lanes" |

## Open questions

- ADR-010-05 and ADR-010-06 were decided on 2026-11-10 (Option A for both); no open decisions remain.
- Dependency risk: 001 has no plan yet and `CaseWorkflow` doesn't exist (`benefit-be:apps/worker/workflows/` has only `smoke.py`, `calendar.py`). 010 builds `review.py` as a module `CaseWorkflow` composes, tested with a minimal test workflow until 001 lands.

## Complexity Tracking

None: no constitution violations.
