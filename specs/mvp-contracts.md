# MVP contracts: what is agreed before the split

Drafted 2026-11-11 for the no-AI MVP (002, 004a, 007, 011; 008 if time allows). Merge these
contracts as one contracts PR in each repo **before** anyone starts their seat. Every lane
reviews that PR (constitution, "Shared interfaces"). Overrule any decision below in that review,
not halfway through the build.

Names below that already exist on `main` are marked *(exists)*. Everything else is new.

## 1. Who owns which shared file

Three of the four MVP specs are in the Workflows lane. All three would otherwise edit the same
files, so the rules are:

| File | Owner | Others |
|---|---|---|
| `benefit-be/apps/worker/workflows/case.py` | 011 seat | 002 and 007 put their logic in their own modules (below) and call it from the hook the contracts PR adds. They never edit `case.py`. |
| `benefit-be/packages/domain/**` | contracts PR only | A change found mid-build goes in a small PR that every seat reviews |
| `benefit-be/apps/api/main.py` (router registration) | contracts PR | Each feature has its own router file |
| `benefit-be/openapi/openapi.json` (committed OpenAPI) | contracts PR adds every MVP endpoint; each feature fills in its own | Regenerate in the feature PR and rebase if another PR changed it |
| `benefit-fe/src/app/router.tsx` | contracts PR adds every MVP route with a placeholder page | Each feature replaces its own placeholder |
| `benefit-fe/src/features/caseworker/case-page/sections.tsx` | contracts PR adds one entry per new section | Each feature writes only its own section component |
| `benefit-be/db/seeds/**`, `db/migrations/**` | seed-data seat ([mvp-seed-data-tasks.md](mvp-seed-data-tasks.md)) | |

Workflow modules for each feature:

| Feature | Module | Called from `case.py` |
|---|---|---|
| 002 | `apps/worker/activities/verification.py` *(exists, stub)* and `apps/worker/workflows/verification_branch.py` | after `verify_documents`: findings → Verification review; missing items → 011's request for information |
| 011 | `apps/worker/workflows/applicant_wait.py`, `apps/worker/activities/notices.py`, `apps/worker/activities/explanations.py` | owned by 011 |
| 007 | `apps/worker/workflows/redetermination.py`, `apps/worker/activities/renewal.py` | at start when `case_type` is `redetermination` |

New branches in `case.py` use `workflow.patched` (TW-7).

## 2. Domain changes (`packages/domain/`)

### Notices (011, FR-011-06)

`NoticeType` *(exists: `approval`, `denial`)* gets every type in FR-011-06:

```
approval, automatic_renewal, renewal_after_response,      # delivered directly
denial, coverage_ended, request_for_information,           # wait for caseworker approval
redetermination_form
```

- `NOTICE_NEEDS_APPROVAL: dict[NoticeType, bool]` is a data table next to the enum. The API and
  the worker read the same table.
- `NoticeStatus`: `pending_approval`, `delivered`.
- `Notice`: `notice_id`, `case_id`, `household_id`, `notice_type`, `status`, `text`,
  `items: list[RequestedItem]` (requests and forms only), `due_case_date: date | None`,
  `created_at`, `delivered_at`, `synthetic`.
- `RequestedItem`: `item_id`, `kind` (`pay_stub`, `confirm_member`, `confirm_job`,
  `confirm_income`), `member_id`, `job_id | None`, `label` (text shown to the applicant).

### Verification result (002, FR-002-23)

`VerificationOutcome` *(exists)* becomes `VerificationResult`. It keeps `complete` and
`needs_review`, so `case.py` keeps working, and adds the rest:

```
VerificationResult:
  case_id: UUID
  identity_verified: bool
  findings: list[Finding]          # needs_review == bool(open findings)
  missing_items: list[MissingItem] # complete == not missing_items
  complete: bool
  needs_review: bool

Finding:
  finding_id: UUID                 # uuid5(case_id, cause, member_id, job_id) so re-runs are identical
  cause: income_mismatch | different_person | conflicting_stubs | identity_mismatch
  member_id: UUID | None
  job_id: UUID | None
  document_id: UUID | None
  declared_monthly: Decimal | None
  documented_monthly: Decimal | None
  conversion: str | None           # e.g. "weekly 300.00 × 52 ÷ 12 = 1300.00"
  dismissed: Dismissal | None      # reason, actor, time

MissingItem:
  member_id: UUID
  job_id: UUID
  kind: no_stub | stub_too_old
```

`VerificationRequest` *(exists)* adds `as_of_date: date`: the received date for an
application, or the redetermination start date. FR-002-15 measures stub age from it.

**How the result routes the case (002 + 011):**

1. Any open finding → a "Verification review" task (FR-010-01). The determination waits for it.
2. No open findings, missing items, and no request for information sent yet on the case → 011
   produces the request for information (FR-011-12) and holds it for approval.
3. No open findings, missing items, and the one automatic request already used → determine. The
   rules then return "Cannot determine", which already goes to review (FR-010-04).
4. Otherwise → determine.

**No identity record.** If the reference lookup has no record for a member, the check records
an `identity_mismatch` finding with the text "no identity record". When a caseworker dismisses
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

lookup_reference(scope, member_id, given_name, family_name, date_of_birth) -> ReferenceAnswer
```

The lookup is a worker repository over the household-scoped `reference_records` collection
(seed task S-01). Matching is exact, on case-folded name and date of birth.

### Explanations (004a, FR-004-10, FR-004-19)

```
Citation:            rule_id, section, title, manual_version
DecisionExplanation: determination_id, case_id, household_id, audience (applicant | caseworker),
                     result, text, citations: list[Citation], built_at, synthetic
explain_determination(determination, audience) -> DecisionExplanation
```

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
| `applicant_response` | signal | `response_id`, `notice_id` (the request or form answered), `snapshot_id \| None`, `document_ids`, `submitted_at_real` | 011 (007 reuses it) |
| `advance_clock` | signal | `action_id`, `requested_by`, `requested_at_real`. The workflow ignores it unless the case clock is in the demo profile. | 011 (replaces the stand-in in `review_ports.py`) |
| `status` *(exists)* | query | adds `pending_timer: {name, due_case_time} \| None` | 011 |
| `response_deadline` | timer | 15 days, `RESPONSE_WINDOW_DAYS` | 011 |
| `redetermination_response_deadline` | timer | 30 days, `REDETERMINATION_RESPONSE_DAYS`, using 011's wait helper | 007 |
| `review_reminder`, `review_escalation` *(exist)* | timer | 2 and 4 days | 010 |
| `coverage_end` *(exists as `coverage_end_passes`)* | timer | Chicago midnight after the coverage end; escalates an open redetermination review and sets the coverage period to `continued_pending_review` | 010, used by 007 |

The API writes data first (documents, pay stub details, the new snapshot) and then sends a
signal that only refers to it.

### Redeterminations (007, FR-007-07, FR-007-10)

- `CaseStart` *(exists)* adds `coverage_period_id: UUID | None`, required when `case_type` is
  `redetermination`.
- A redetermination's `case_id` is `uuid5(coverage_period_id, "redetermination")`, so
  `workflow_id_for(case_id)` *(exists)* gives one workflow ID per coverage period. A second
  start gets Temporal's "already started", and the API answers with a link to the running case.
  This keeps FR-007-07 now that FR-007-15 (the schedule) is deferred.
- `CaseOutcome` already has `renewed_automatically`, `renewed_after_response` and
  `ended_by_caseworker`. `CoverageStatus` already has `continued_pending_review`. Neither
  changes.

## 3. REST API (stubbed in the contracts PR, filled in by each feature)

| Method and path | Who | Feature |
|---|---|---|
| `POST /cases/{case_id}/documents` (multipart: file and pay stub details) | applicant (own case) | 002 |
| `GET /cases/{case_id}/verification` | caseworker, supervisor | 002 |
| `POST /cases/{case_id}/review-tasks/{task_id}/actions` *(exists)* | caseworker | 002 uses `correct_value` and `dismiss_finding` |
| `GET /cases/{case_id}/determinations` *(exists)* | caseworker, supervisor | 004a adds `explanations` to each item |
| `GET /me/history` | applicant | 004a |
| `GET /me/notices`, `GET /me/notices/{notice_id}` | applicant (delivered only) | 011 |
| `GET /me/requests` | applicant (open requests and renewal forms) | 011 (007b adds forms) |
| `POST /me/requests/{notice_id}/response` (multipart) | applicant | 011 (007b reuses it) |
| `POST /cases/{case_id}/advance-clock` | supervisor, demo profile only | 011 |
| `GET /households/{household_id}` | caseworker, supervisor | 007 |
| `POST /households/{household_id}/redeterminations` → `201` new or `200` with the running case | caseworker, supervisor | 007 |
| `GET /metrics?month=YYYY-MM` | caseworker, supervisor | 008 |

Notices and forms that need approval are approved with the existing review-task actions route:
a `notice_approval` task (FR-010-01, as revised) with the action `approve_notice`.

## 4. Review reasons for the MVP (010)

FR-010-01 as revised on 2026-11-11 (see 010's spec):

- **Notice approval**: raised when a request for information or redetermination form is ready.
  One action, `approve_notice` (added to `ActionType`) → delivered. "Edit and approve" is
  deferred.
- **Verification review**: the causes are the four 002 finding causes, plus the retry limit
  being reached (FR-010-03).
- **Explanation review**: not raised in the MVP. The enum value stays.

## 5. Database (`db/migrations/versions/0006_mvp.py`, Knowledge & data)

New collections, each household-scoped with `household_id` (and `case_id` where it belongs to a
case): `pay_stub_details`, `findings` (or embedded in `verification_results`, whichever 002's
plan prefers, as long as it is decided in the contracts PR), `verification_results`,
`reference_records`, `notices`, `applicant_responses`, `decision_explanations`. Indexes:
`notices (household_id, status, created_at)`, `reference_records (household_id, member_id)`.
The existing `outbox` keeps its role of delivering notices.

## 6. Frontend (benefit-fe)

Placeholder routes in the contracts PR, filled in by each feature:

| Route | Feature |
|---|---|
| `applicant/apply` *(exists)*: pay stub upload and details in `JobFields` | 002 |
| `applicant/notices`, `applicant/notices/:noticeId` | 011 |
| `applicant/requests/:noticeId` (respond to a request or renewal form) | 011, 007b |
| `applicant/history` | 004a |
| `caseworker/households/:householdId` | 007 |
| `caseworker/metrics` | 008 |

New case page sections, in this order, each in its own file: `documents` (002), `notices`
(011), `explanation` (004a, inside or after `determination`), `demo-clock` (011, supervisors in
the demo profile only).

## 7. Contracts PR tasks

Each is done together in the first session and merged before the split.

- [ ] C-01 `[contracts]` benefit-be: notice enum and approval table, `Notice`, `RequestedItem`,
      `NoticeStatus` (section 2)
- [ ] C-02 `[contracts]` benefit-be: `VerificationResult`, `Finding`, `MissingItem`,
      `PayStubDetails`, `VerificationRequest.as_of_date`. Update the `verify_documents` stub to
      return an empty result.
- [ ] C-03 `[contracts]` benefit-be: `ReferenceAnswer` and a stub `lookup_reference` that always
      answers `match` with no jobs
- [ ] C-04 `[contracts]` benefit-be: `Citation`, `DecisionExplanation` and a stub
      `explain_determination` that returns the rule trace
- [ ] C-05 `[contracts]` benefit-be: `applicant_response` and `advance_clock` signal payloads,
      `pending_timer` on `status`, timer name constants, and the two new window settings in
      `packages/platform/settings.py` and `.env.example`
- [ ] C-06 `[contracts]` benefit-be: `CaseStart.coverage_period_id`, redetermination `case_id`
      rule, `ActionType.approve_notice`, revised review reason table
- [ ] C-07 `[contracts]` benefit-be: `case.py` hooks (patched) calling 002's verification branch,
      011's wait and notice steps, and 007's redetermination path, each a stub that does what
      main does today. Workflow replay test still green.
- [ ] C-08 `[contracts]` benefit-be: every endpoint in section 3 registered, returning `501`,
      and the OpenAPI file regenerated and committed
- [ ] C-09 `[data]` benefit-be: migration `0006_mvp` (section 5)
- [ ] C-10 `[contracts]` benefit-fe: regenerated API client, placeholder routes and case page
      sections (section 6)
- [ ] C-11 `[contracts]` metarepo: tick this list and link the two PRs from `specs/README.md`

Done when: both PRs are merged, `make test` and the frontend checks pass on `main`, and each
seat can run its first failing test against the stubs.
