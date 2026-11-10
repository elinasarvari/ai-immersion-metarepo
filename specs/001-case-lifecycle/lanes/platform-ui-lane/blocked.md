# platform-ui-lane: changes needed outside this lane

1. **[contracts] T004 / T022 — regenerate `openapi/openapi.json`.** The three routes now exist
   (`submitApplication`, `getCase`, `submitReviewAction` in `apps/api/routers/applications.py`,
   `apps/api/routers/cases.py`), so `make openapi-check` fails until `make openapi` is run and the
   result is compared with `contracts/rest-api.openapi.yaml`. Expected differences for the contracts
   lane to accept or reconcile:
   - The security scheme is the existing `sessionCookie` (cookie `benefit_session`) from
     `apps/api/main.py`, not the yaml's placeholder `session` (cookie `session`).
   - Error responses document `ErrorEnvelope`. `getCase` and `submitReviewAction` also list
     401/403/404/422 (and 503 for the action route), which the yaml leaves out.
   - `submitApplication` returns 201, and 200 for the same reference again (set at runtime). The 200
     is declared under `responses`.
2. **[workflows] contract names used by the API** (`apps/api/temporal_client.py`): workflow type
   `CaseWorkflow`, signal `caseworker_action` (payload `CaseworkerActionRequest`), query
   `allowed_actions` (→ `AllowedActions`), started with `id_reuse_policy=REJECT_DUPLICATE`, so a
   retried submission never re-runs a decided case. When the pre-check refuses an action, the API
   still signals it (best effort) and returns 409, so the workflow records `action_rejected`
   (US1-AS5). `CaseWorkflow` must therefore treat a signal for a non-open or other task as a
   rejection, never as an error.
3. **[qa] T045 (TC-68/69):** the API maps `DuplicateKeyError` on `household_open_unique` (key
   `household_id`) to `household_has_open_case`, and on `_id` / `submission_reference_unique` to
   "return the existing case". This needs the real replica set to verify under concurrency.
