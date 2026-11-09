# Workflows lane: Temporal (`TW-*`)

Applies to `benefit-be/apps/worker/`. Owner: Workflows.

## Workflows (`apps/worker/workflows/`)
- **TW-1** Workflows are deterministic orchestration only. No I/O, network, DB, file access, LLM calls, `datetime.now()`, `time.time()`, `random`, `uuid4()`, threads or environment reads. Use `workflow.now()`, `workflow.random()`, `workflow.uuid4()` and timers.
- **TW-2** Every side effect is an activity. A workflow never imports `packages/agents`, `packages/rag` or DB code; it calls activities by name.
- **TW-3** One `CaseWorkflow` per case, with the workflow ID derived from the case ID, so starting it twice is idempotent.
- **TW-4** Human review points are durable waits in the workflow (signal plus `workflow.wait_condition`, with a timer for deadlines). Never wait inside an agent or an activity.
- **TW-5** Caseworker actions arrive as signals. Read-only state is exposed through queries. Signal and query payloads are `packages/domain` models.
- **TW-6** `RenewalWorkflow` is started by a Temporal Schedule, not a cron job or the API. The renewal is automatic when nothing is missing. Otherwise the workflow creates a pre-filled request.
- **TW-7** Changing workflow code that already has running executions uses `workflow.patched()` (or a new workflow type). Never change the order of commands in place.
- **TW-8** Deadlines and waits use Temporal timers, so time-skipping tests can control them.

## Activities (`apps/worker/activities/`)
- **TW-9** Activities are thin: translate the input, call one package function, return the result. No business logic.
- **TW-10** Every activity has an explicit `start_to_close_timeout` and a retry policy. Non-retryable errors (validation, permission) are marked non-retryable.
- **TW-11** Activities are idempotent, because Temporal may run them more than once.
- **TW-12** Models (LLM clients, embeddings, rerankers) are loaded once per worker process, not per activity call.

## Tests
- **TW-13** Every workflow has a time-skipping test that covers the happy path, each signal, and each deadline timer.
- **TW-14** Every workflow change adds or updates a replay test against a recorded history.
- **TW-15** Workflow tests stub the activities. They never call real agents, the DB or the Anthropic API.
- **TW-16** A crash test proves a workflow resumes correctly after the worker restarts.

## Logging
- **TW-17** Use `workflow.logger` inside workflows. Activities use `structlog` and include `case_id` and `workflow_id`.
