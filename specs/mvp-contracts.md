# MVP contracts: what is agreed before the split

Drafted 2026-11-11 for the no-AI MVP (002, 004a, 007, 011; 008 if time allows). Merge these
contracts as one contracts PR in each repo **before** anyone starts their seat. Every lane
reviews that PR (constitution, "Shared interfaces"). Overrule any decision below in that review,
not halfway through the build.

Names below that already exist on `main` are marked *(exists)*. Everything else is new.

**Status (2026-11-11):** C-01 to C-10 are built on branch `feature/mvp-contracts` in both repos,
not pushed yet. Where the build differs from the first draft, this document now says what was
built. 007b is dropped, so the redetermination form and its 30-day timer are not in the
contract. The changes from the draft are listed in section 8.

## 1. Who owns which shared file

Three of the four MVP specs are in the Workflows lane. All three would otherwise edit the same
files, so the rules are:

| File | Owner | Others |
|---|---|---|
| `benefit-be/apps/worker/workflows/case.py` | 011 seat | 002 and 007 put their logic in their own modules (below). 011 calls them from `case.py` as each lands. 002 and 007 never edit `case.py`. |
| `benefit-be/packages/domain/**` | contracts PR only | A change found mid-build goes in a small PR that every seat reviews |
| `benefit-be/apps/api/main.py` (router registration) | contracts PR | Each feature has its own router file |
| `benefit-be/openapi/openapi.json` (committed OpenAPI) | contracts PR adds every MVP endpoint; each feature fills in its own | Regenerate in the feature PR and rebase if another PR changed it |
| `benefit-fe/src/app/router.tsx` | contracts PR adds every MVP route with a placeholder page | Each feature replaces its own placeholder |
| `benefit-fe/src/features/caseworker/case-page/sections.tsx` | contracts PR adds one entry per new section | Each feature writes only its own section component |
| `benefit-be/db/seeds/**`, `db/migrations/**` | seed-data seat ([mvp-seed-data-tasks.md](mvp-seed-data-tasks.md)) | |

Workflow modules for each feature:

| Feature | Module | Called from `case.py` |
|---|---|---|
| 002 | `apps/worker/activities/verification.py` *(exists, stub)*, `apps/worker/workflows/verification_branch.py` (`next_step`, built), `apps/worker/repositories/reference_records.py` (stub) | after `verify_documents`: findings → Verification review; missing items → 011's request for information |
| 011 | `apps/worker/workflows/applicant_wait.py`, `apps/worker/activities/notices.py`, `apps/worker/activities/explanations.py` | owned by 011 |
| 007a | `apps/worker/workflows/redetermination.py`, `apps/worker/activities/renewal.py` | at start when `case_type` is `redetermination` |

The contracts PR adds no hooks to `case.py`. A hook with no behaviour behind it would only be
dead code. 011 adds each call when the behaviour exists, and new branches use
`workflow.patched` (TW-7).

## 2. Domain changes (`packages/domain/`)

### Notices (011, FR-011-06)

`NoticeType` *(exists: `approval`, `denial`)* gets every type in FR-011-06:

```
approval, automatic_renewal, renewal_after_response,      # delivered directly
denial, coverage_ended, request_for_information            # wait for caseworker approval
```

- No `redetermination_form`: 007b is dropped.
- `NOTICE_NEEDS_APPROVAL` in `packages/domain/notice.py` says which types wait. The API and the
  worker read the same table.
- `NoticeStatus`: `pending_approval`, `delivered`.
- `Notice`: `id` (stored as `_id`, `uuid5(case_id, notice_type)`; the API calls it `notice_id`), `case_id`, `household_id`, `notice_type`, `status`, `text`,
  `items: list[RequestedItem]` (requests and forms only), `due_case_date: date | None`,
  `created_at`, `delivered_at`, `synthetic`.
- `RequestedItem`: `item_id`, `kind` (`pay_stub`, `confirm_member`, `confirm_job`,
  `confirm_income`), `member_id`, `job_id | None`, `label` (text shown to the applicant).

### Verification result (002, FR-002-23)

`VerificationOutcome` *(exists)* becomes `VerificationResult`, in
`packages/domain/verification.py` (with `VerificationRequest`). It keeps `complete` and
`needs_review`, and every new field has a default, so recorded workflow histories still replay:

```
VerificationResult:
  case_id: UUID | None
  identity_verified: bool | None       # None: the check did not look (the 001 stub)
  findings: list[Finding]              # needs_review == bool(open findings)
  missing_items: list[MissingDocument] # complete == not missing_items
  complete: bool
  needs_review: bool

Finding:
  finding_id: UUID                 # uuid5(case_id, cause, member_id, job_id, document_id): re-runs give
                                   # the same ID, and two "different person" stubs differ
  cause: income_mismatch | different_person | conflicting_stubs | identity_mismatch
  member_id: UUID | None
  job_id: UUID | None
  document_id: UUID | None
  identity: match | no_match | no_record | None   # identity mismatches only
  declared_monthly: Decimal | None
  documented_monthly: Decimal | None
  conversion: str | None           # e.g. "weekly 300.00 × 52 ÷ 12 = 1300.00"
  dismissed: Dismissal | None      # reason, actor, time

MissingDocument:                   # named apart from 003's MissingItem
  member_id: UUID
  job_id: UUID
  kind: no_stub | stub_too_old
```

`VerificationRequest` *(exists)* adds `as_of_date: date | None`: the received date for an
application, or the redetermination start date. FR-002-15 measures stub age from it. It is
optional only so that old histories decode; `case.py` always sends it.

The routing below is built as `next_step(result, *, request_already_sent)` in
`apps/worker/workflows/verification_branch.py`.

**How the result routes the case (002 + 011):**

1. Any open finding → a "Verification review" task (FR-010-01). The determination waits for it.
2. No open findings, missing items, and no request for information sent yet on the case → 011
   produces the request for information (FR-011-12) and holds it for approval.
3. No open findings, missing items, and the one automatic request already used → determine. The
   rules then return "Cannot determine", which already goes to review (FR-010-04).
4. Otherwise → determine.

**No identity record.** If the reference lookup has no record for a member, the check records
an `identity_mismatch` finding with `identity: no_record`. When a caseworker dismisses
an `identity_mismatch` finding (with a reason), that member counts as identity verified.

### Pay stub details (002, FR-002-21)

`PayStubDetails`: `document_id`, `case_id`, `household_id`, `member_id | None` (matched from
`employee_name`), `employee_name`, `employer`, `frequency` (existing `PayFrequency`),
`gross_pay`, `pay_date`, `corrections: list[Correction]`. Pay stubs that the applicant entered
for the case replace the seeded verifications as the `VerifiedFacts` source *(exists, seam in
`apps/worker/repositories/verified_facts.py`)*. A household with no entered stubs (seeded
history) keeps reading `seeded_verifications`.

### Reference lookup (002, FR-002-22)

```
ReferenceAnswer:
  member_id: UUID
  identity: match | no_match | no_record
  jobs: list[ReferenceJob]   # employer, monthly_gross

ReferenceRecords.lookup(scope, ReferenceLookup) -> ReferenceAnswer
ReferenceLookup: household_id, member_id, given_name, family_name, date_of_birth
```

The lookup is a worker repository (`apps/worker/repositories/reference_records.py`) over the
household-scoped `reference_records` collection (seed task S-01). The contracts PR has the
protocol and `StubReferenceRecords` (always `match`, no jobs). Matching is exact, on case-folded
name and date of birth.

### Explanations (004a, FR-004-10, FR-004-19)

```
Citation:            rule_id, section, title, manual_version
DecisionExplanation: determination_id, case_id, household_id, audience (applicant | caseworker),
                     result, text, citations: list[Citation], built_at, synthetic
explain_determination(record: DeterminationRecord, audience) -> DecisionExplanation
```

It takes the stored `DeterminationRecord`, not the bare determination: the explanation needs its
IDs, and `built_at` is the record's time, so the function stays pure (FR-004-19).

- A pure function in `packages/rules/explanations.py`, owned by Knowledge & data. It reads
  `CITATIONS` in `packages/rules/citations.py`.
- 011 calls it from `apps/worker/activities/explanations.py` right after the determination is
  stored. 011 stores both audiences in `decision_explanations`.
- Until 004a lands, a stub returns the rule trace (FR-011-07). The stub keeps the same
  signature.
- Seeded history explanations use the same shape (seed task S-06).

### Signals, timers and queries (011, 007)

| Name | Kind | Payload / value | Owner |
|---|---|---|---|
| `caseworker_action` *(exists)* | signal | `CaseworkerActionSignal` | 010 |
| `applicant_response` | signal | `ApplicantResponseSignal`: `response_id`, `notice_id` (the request answered), `snapshot_id \| None`, `document_ids`, `submitted_at_real` | 011 |
| `advance_clock` | signal | `AdvanceClockSignal`: `action_id`, `requested_by`, `requested_at_real`. The workflow ignores it unless the case clock is in the demo profile. | 011 (replaces the stand-in in `review_ports.py`) |
| `status` *(exists)* | query | adds `pending_timer: {name, due_case_time} \| None` | 011 |
| `response_deadline` | timer | 15 days, `RESPONSE_WINDOW_DAYS` | 011 |
| `review_reminder`, `review_escalation` *(exist)* | timer | 2 and 4 days | 010 |
| `coverage_end` *(exists as `coverage_end_passes`)* | timer | Chicago midnight after the coverage end; escalates an open redetermination review and sets the coverage period to `continued_pending_review` | 010, used by 007 |

Payloads and `TimerName` are in `packages/domain/waits.py`. The signals are not registered
on `CaseWorkflow` yet (011 adds them with their handlers; the workflow contract test lists
registered signals). The API writes data first (documents, pay stub details, the new snapshot) and then sends a
signal that only refers to it.

### Redeterminations (007, FR-007-07, FR-007-10)

- `CaseStart` *(exists)* adds `coverage_period_id: UUID | None`, required when `case_type` is
  `redetermination`.
- A redetermination's `case_id` is `redetermination_case_id(household_id,
  coverage_period_id)` (a uuid5 of both, as TW-6 asks), so
  `workflow_id_for(case_id)` *(exists)* gives one workflow ID per coverage period. A second
  start gets Temporal's "already started", and the API answers with a link to the running case.
  This keeps FR-007-07 now that FR-007-15 (the schedule) is deferred.
- `CaseOutcome` already has `renewed_automatically`, `renewed_after_response` and
  `ended_by_caseworker`. `CoverageStatus` already has `continued_pending_review`. Neither
  changes.

## 3. REST API (stubbed in the contracts PR, filled in by each feature)

| Method and path | Who | Feature |
|---|---|---|
| `POST /cases/{case_id}/documents` (JSON: pay stub details, type and size) → `document_id` | applicant (own case) | 002 |
| `PUT /cases/{case_id}/documents/{document_id}/content` (raw PDF, PNG or JPEG bytes, up to 10 MB) | applicant (own case) | 002 |
| `GET /cases/{case_id}/verification` | caseworker, supervisor | 002 |
| `POST /cases/{case_id}/review-tasks/{task_id}/actions` *(exists)* | caseworker | 002 uses `correct_value` and `dismiss_finding` |
| `GET /cases/{case_id}/explanations` | caseworker, supervisor | 004a |
| `GET /me/history` | applicant | 004a |
| `GET /me/notices`, `GET /me/notices/{notice_id}` | applicant (delivered only) | 011 |
| `GET /me/requests` | applicant (open requests for information) | 011 |
| `POST /me/requests/{notice_id}/response` (JSON: uploaded `document_ids`, confirmed items) | applicant | 011 |
| `POST /cases/{case_id}/advance-clock` | supervisor, demo profile only | 011 |
| `GET /households/{household_id}` | caseworker, supervisor | 007 |
| `POST /households/{household_id}/redeterminations` → `201` new or `200` with the running case | caseworker, supervisor | 007 |
| `GET /metrics?month=YYYY-MM` | caseworker, supervisor | 008 |

Bodies and responses are in `apps/api/schemas/mvp.py`. Every stub answers `501` with error code
`not_implemented` (new) for its allowed role, and `403` for others.

Notices that need approval are approved with the existing review-task actions route: a
`notice_approval` task with the existing action `approve`.

## 4. Review reasons for the MVP (010)

FR-010-01 as revised on 2026-11-11 (see 010's spec):

- **Notice approval**: raised when a request for information is ready. Action `approve`
  *(exists)* → delivered. "Edit and approve" is not offered. 010's table stays as it is;
  `CaseWorkflow` uses its own interim table (`CASE_WORKFLOW_ACTIONS`), and 011 adds
  `notice_approval: (approve,)` to it when it raises these tasks.
- **Verification review**: the causes are the four 002 finding causes, plus the retry limit
  being reached (FR-010-03). `ReviewCause` gains `income_mismatch` and `conflicting_stubs`;
  `different_person` and `identity_mismatch` already exist.
- **Explanation review**: not raised in the MVP. The enum value stays.

## 5. Database (`db/migrations/versions/0006_mvp.py`, Knowledge & data)

New collections, each household-scoped with `household_id` (and `case_id` where it belongs to a
case): `pay_stub_details`, `verification_results` (findings are embedded),
`reference_records` (household only), `notices`, `applicant_responses`,
`decision_explanations`. They start with minimal validators; each feature tightens its own.
Indexes: `pay_stub_details (document_id)` unique and `(case_id)`, `verification_results (case_id)`
unique, `notices (household_id, status, created_at)` and `(case_id, created_at)`, `applicant_responses (case_id, notice_id)`,
`decision_explanations (determination_id, audience)` unique and `(case_id)`,
`reference_records (household_id, member_id)` unique. All are in the scope registry
(`packages/platform/scope.py`). The existing `outbox` keeps its role of delivering notices.

## 6. Frontend (benefit-fe)

Placeholder routes in the contracts PR, filled in by each feature:

| Route | Feature |
|---|---|
| `applicant/apply` *(exists)*: pay stub upload and details in `JobFields` | 002 |
| `applicant/notices`, `applicant/notices/:noticeId` | 011 |
| `applicant/requests/:noticeId` (respond to a request) | 011 |
| `applicant/history` | 004a |
| `caseworker/households/:householdId` | 007a |
| `caseworker/metrics` | 008 |

Each placeholder route renders `PlaceholderPage`. The case page sections are registered in this
order: `status`, `review-task`, `documents` (002), `determination`, `explanation` (004a),
`notices` (011), `demo-clock` (011, supervisors in the demo profile only), `history`. Each new
one is a hidden `PendingSection` until its feature swaps in its own component file.

## 7. Contracts PR tasks

Each is done together in the first session and merged before the split.

- [x] C-01 `[contracts]` benefit-be: notice enum and approval table, `Notice`, `RequestedItem`,
      `NoticeStatus` (section 2)
- [x] C-02 `[contracts]` benefit-be: `VerificationResult`, `Finding`, `MissingItem`,
      `PayStubDetails`, `VerificationRequest.as_of_date`. (`MissingItem` is built as `MissingDocument`.) Update the `verify_documents` stub to
      return an empty result.
- [x] C-03 `[contracts]` benefit-be: `ReferenceAnswer` and a stub `lookup_reference` that always
      answers `match` with no jobs
- [x] C-04 `[contracts]` benefit-be: `Citation`, `DecisionExplanation` and a stub
      `explain_determination` that returns the rule trace
- [x] C-05 `[contracts]` benefit-be: `applicant_response` and `advance_clock` signal payloads,
      `pending_timer` on `status`, timer name constants, and `RESPONSE_WINDOW_DAYS` in
      `packages/platform/settings.py` and `.env.example`
- [x] C-06 `[contracts]` benefit-be: `CaseStart.coverage_period_id`, redetermination `case_id`
      rule, review causes (the existing `approve` action is used for notices)
- [x] C-07 `[contracts]` benefit-be: `case.py` sends `as_of_date` and reads `VerificationResult`;
      `next_step` routing built and tested. No other hooks (section 1). Replay tests green.
- [x] C-08 `[contracts]` benefit-be: every endpoint in section 3 registered, returning `501`,
      and the OpenAPI file regenerated and committed
- [x] C-09 `[data]` benefit-be: migration `0006_mvp` (section 5)
- [x] C-10 `[contracts]` benefit-fe: regenerated API client, placeholder routes and case page
      sections (section 6)
- [ ] C-11 `[contracts]` metarepo: tick this list and link the two PRs from `specs/README.md`

## 8. Changes from the first draft

| Draft | Built | Why |
|---|---|---|
| `approve_notice` action | existing `approve` | 010 already has it for notice approval |
| `MissingItem` | `MissingDocument` | 003's `MissingItem` is already an OpenAPI schema; two would clash |
| `explain_determination(determination, audience)` | `(record, audience)` | needs IDs and a fixed `built_at` to stay pure |
| Multipart upload | JSON details, then raw bytes to `.../content` | no multipart dependency (`python-multipart`) is installed; this adds none |
| `explanations` on `GET .../determinations` | `GET /cases/{case_id}/explanations` | leaves 003's endpoint and contract unchanged |
| Stub hooks in `case.py` for 002, 011, 007 | none; 011 wires them | hooks with no behaviour would be dead code |
| Redetermination form, 30-day timer | dropped | 007b is dropped |
| Redetermination ID from the coverage period | from household and coverage period | TW-6 |

Done when: both PRs are merged, `make test` and the frontend checks pass on `main`, and each
seat can run its first failing test against the stubs.
