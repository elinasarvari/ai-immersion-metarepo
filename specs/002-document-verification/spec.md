# Feature Specification: Pay Stub Upload and Income Check

**Feature Branch**: `feature/002-document-verification`

**Created**: 2026-11-09

**Status**: Draft (MVP scope, 2026-11-11: all AI removed)

**Input**: User description: "Verification of uploaded income documents against declared information". Originally AI extraction and drafting; the MVP replaces them with details typed by the applicant and a fixed calculation.

## Lane & Dependencies

- **Lane**: Workflows (the check runs as a workflow step). Was Agents; that lane has no MVP work.
- **Provides**: pay stub upload; a verification result for a case (entered pay stub details,
  findings, missing items, whether review is needed); the identity and income reference lookup;
  the screens to upload pay stubs and to check and correct the result. Used by 001, 007, 010
  and 011.
- **Depends on**: 001 (the application form and the case page), 003 (monthly income formula
  FR-003-18, synthetic households and pay stubs), 010 ("Verification review" tasks). All are
  on `main`, so this feature can start immediately.
- **Out of scope**: reading documents automatically; identity documents; documents not in
  English; document types other than pay stubs; making any eligibility decision.

Story and requirement IDs are not reused. Removed ones are listed under "Removed and moved".

## User Scenarios & Testing *(mandatory)*

### User Story 5 - Applicant uploads pay stubs and enters their details (Priority: P1)

An applicant attaches their pay stubs to the application and types the key details of each
one. The files and details are stored with the case.

**Why this priority**: The income check has nothing to work on without them.

**Independent Test**: In the browser, sign in as a demo applicant, submit an application with a
pay stub and its details, then sign in as a caseworker and see the document, the details and
the check result on the case page.

**Acceptance Scenarios**:

1. **Given** the application form, **When** the applicant attaches pay stubs (PDF, PNG or JPEG, up
   to 10 MB each, up to 10 files), enters each stub's details and submits, **Then** the files
   and details are stored with the case and listed on the confirmation and on the case page.
2. **Given** a file that is too large, of an unsupported type, or an 11th file, **When** it is
   attached, **Then** it is refused with the allowed sizes and types, and the rest of the form is
   kept.
3. **Given** an attached pay stub with a detail left empty, **When** the applicant submits,
   **Then** the form names the missing detail and nothing is lost.

---

### User Story 2 - Find mismatches with declared income (Priority: P1)

The system compares the income shown by the pay stub details with what the applicant declared
and records a finding when they differ.

**Why this priority**: Catching discrepancies is the main value for caseworkers.

**Independent Test**: Run the seeded mismatch households and confirm every difference above the
threshold produces a finding showing both values, and no household within it does.

**Acceptance Scenarios**:

1. **Given** declared monthly income and pay stub details showing income more than 10%
   different, **When** they are compared, **Then** a finding is recorded with both values and the
   pay stub it came from, and a "Verification review" task is raised.
2. **Given** a difference of 10% or less, **When** they are compared, **Then** no mismatch finding
   is recorded.
3. **Given** a weekly or bi-weekly pay stub, **When** it is compared, **Then** income is converted
   to a monthly figure before comparing, and the conversion is shown in the finding.
4. **Given** a declared job with no pay stub, or whose latest stub is too old, **When** the check
   runs, **Then** the job is listed as missing information and no mismatch finding is recorded
   for it.

---

### User Story 6 - Caseworker checks and corrects the result (Priority: P1)

A caseworker opens a case and sees the uploaded documents, the details the applicant entered
and each finding. They can correct a detail against the document or dismiss a finding, with a
reason.

**Why this priority**: The applicant may mistype; the caseworker has the document in front of
them.

**Independent Test**: In the browser, open a seeded case with a mismatch finding as a caseworker,
open the pay stub, correct the gross pay with a reason, and confirm the check runs again and the
correction is recorded.

**Acceptance Scenarios**:

1. **Given** a checked case, **When** the caseworker opens it, **Then** they see the uploaded
   documents, each stub's entered details, and each finding with the values compared.
2. **Given** an entered detail, **When** the caseworker corrects it, **Then** a reason is required,
   the correction is recorded with reviewer and time, and the check runs again with the new
   value.
3. **Given** a finding, **When** the caseworker dismisses it, **Then** a reason is required and the
   dismissal is recorded with reviewer and time.

### Edge Cases

- Several pay stubs for the same job: the most recent one sets monthly income (FR-003-18);
  stubs for the same pay period with different gross pay produce a finding.
- The name on a pay stub matches no household member: a "different person" finding is recorded
  and the stub is not used as income.
- The applicant's name and date of birth don't match the reference record: an "identity
  mismatch" finding is recorded and the case needs review.
- A member declares zero income: no document is needed.
- An upload is too large or an unsupported type: it is refused with the allowed sizes and types,
  and the rest of the form is kept.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-002-03**: For each household member with income, when declared monthly income differs
  from documented monthly income (worked out from the entered pay stub details as in
  FR-003-18) by more than 10%, the system MUST record a finding showing both values and the
  pay stub used.
- **FR-002-08**: The check MUST NOT produce an eligibility decision.
- **FR-002-14**: The employee name entered for each pay stub MUST be matched to a household
  member. A stub that matches no member MUST record a "different person" finding and is not
  used as income.
- **FR-002-15**: A declared job with no pay stub, or whose most recent stub is dated more than 45
  days before the case was received (for a redetermination: before it started), MUST be treated
  as missing information and listed in the verification result, so that the request for
  information (FR-011-12) names it. A member declaring zero income needs no document.
- **FR-002-16**: Every finding MUST raise the "Verification review" reason in FR-010-01, with
  the specific cause shown on the task: income mismatch, different person, conflicting stubs or
  identity mismatch.
- **FR-002-17**: Applicants MUST be able to attach pay stubs to the application (FR-001-24) or to a
  response (FR-011-10, FR-007-19): PDF, PNG or JPEG, up to 10 MB each, up to 10 files. Other files
  are refused with the allowed sizes and types. (Was FR-006-07, upload part.)
- **FR-002-18**: The case page (FR-001-27) MUST show the case's documents, each stub's entered
  details and each finding with the values compared. (Was FR-006-09, findings and documents
  part.)
- **FR-002-19**: A caseworker MUST be able to correct an entered detail or dismiss a finding. The
  system MUST require a reason and record it with reviewer and time. A corrected detail makes
  the check run again. (Was FR-006-02; revised, no evaluation set.)
- **FR-002-21**: For every attached pay stub the applicant MUST enter the employee name,
  employer, pay frequency (weekly, bi-weekly, semi-monthly, monthly), gross pay and pay date. A
  stub with a detail missing cannot be submitted.
- **FR-002-22**: The system MUST provide a reference lookup that answers, from the synthetic data
  set (003), whether a person's name and date of birth match their identity record, and each
  job's employer and monthly gross income. It is an ordinary lookup with no delays or failures.
  The check uses the identity answer: a match sets "identity verified" for the rules
  (FR-003-01); a non-match records an "identity mismatch" finding. Redeterminations use both
  answers (FR-007-13). (Replaces FR-002-13 and FR-005-12.)
- **FR-002-23**: The check MUST be a single pass with a fixed result: the same case data always
  gives the same verification result. It is offered to the case workflow as
  `verify_documents(case_id) -> VerificationResult`.

### Removed and moved

| ID | What it was | Now |
|---|---|---|
| US1, FR-002-01, FR-002-02 | AI extraction with confidence scores | Removed; the applicant enters the details (FR-002-21) |
| US3, FR-002-05, FR-002-12 | AI-drafted requests for information and renewal forms | Removed; fixed templates in FR-011-12 and FR-007-03 |
| US4, FR-002-04 | Verification loops and the 3-loop limit | Removed; single pass (FR-002-23) |
| FR-002-06, FR-002-07 | Citation checks on AI output; document text as data only | Removed |
| FR-002-09, FR-002-20 | AI run records and the AI activity section | Removed |
| FR-002-10, FR-002-11 | Agent evaluation set and command | Removed |
| FR-002-13 | Checks against simulated verification sources (005) | Replaced by FR-002-22 |
| SC-002-01, SC-002-03, SC-002-04, SC-002-05 | Extraction accuracy, citation, injection and evaluation targets | Removed |

### Key Entities

- **Document**: an uploaded file for a case, with type, upload time and synthetic marker.
- **Pay stub details**: employee name, employer, pay frequency, gross pay and pay date for one
  document, as entered, with any caseworker correction.
- **Finding**: a discrepancy, with its cause, the values compared and any dismissal.
- **Verification result**: findings, missing items, identity verified or not, and whether review
  is needed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-002-02**: 100% of seeded mismatches above 10% are flagged; no seeded household within 10%
  is flagged.
- **SC-002-06**: A demo applicant submits an application with a pay stub in the browser in under 5
  minutes. (Was SC-006-02, together with SC-001-06.)
- **SC-002-07**: Running the check twice on the same case gives identical results.

## Assumptions

- Only pay stubs are in scope.
- The 10% threshold is a team default, adjustable by configuration.
- The synthetic data set (003) holds an identity record and per-job income for every seeded
  person, including the seeded disagreements that 005's simulated sources would have used.
