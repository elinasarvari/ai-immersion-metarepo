# Feature Specification: Decision Explanations and Policy Search

**Feature Branch**: `feature/004-policy-search`

**Created**: 2026-11-09

**Status**: Draft (MVP scope, 2026-11-11: all AI removed)

**Input**: User description: "Search and citation of the Illinois Medicaid policy manual, and plain-language explanations of decisions". The MVP builds explanations from a fixed template and defers search.

## Lane & Dependencies

- **Lane**: Knowledge & data
- **Provides**: a plain-language explanation of every determination, with a policy citation per
  rule, stored with the determination and shown to caseworkers and applicants. Used by 011
  (the explanation in adverse notices).
- **Depends on**: 003 (determinations and the rule-by-rule trace, FR-003-05) and 001 (the case
  page and coverage periods). Both are on `main`, so this feature can start immediately.
- **Who does what**: this feature provides the pure function `explain_determination`
  (`packages/rules/explanations.py`) and the citation table. 011 calls it when a determination
  is stored and saves the result (FR-011-07). This feature writes no workflow code.
- **Seeded history**: seeded explanations on `main` use an older shape. Seed task S-06 in
  [mvp-seed-data-tasks.md](../mvp-seed-data-tasks.md) moves them to `DecisionExplanation`
  ([mvp-contracts.md](../mvp-contracts.md) section 2), so seeded and new explanations look the
  same on screen.
- **Two parts**: **004a Decision explanations** is the MVP and is everything below except the
  "Deferred" section. **004b Policy search** is deferred: with no AI agents nothing in the
  product calls it.
- **Out of scope**: other states' manuals, non-medical chapters, keeping the manual
  automatically up to date, changing or overriding any determination.

Story and requirement IDs are not reused. Removed and deferred ones are listed at the end of
the requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 4 - Explain a decision in plain language (Priority: P1)

For any determination, the applicant and the caseworker can read a plain-language explanation of
the outcome: what each rule found, the values used, and the policy section behind each rule.

**Why this priority**: "Why was this decided?" is central to the demo and to trust in the system.

**Independent Test**: Build explanations for the known-answer determinations and check every
number matches the determination and every rule has a citation.

**Acceptance Scenarios**:

1. **Given** an income-ineligible determination, **When** its explanation is built, **Then** it
   states the outcome, the household income, size and limit used, and cites the policy section
   for the income rule.
2. **Given** any determination, **When** its explanation is built, **Then** every number in it
   is taken from the determination and it states nothing else.
3. **Given** a rule with no entry in the citation table, **When** the explanation is built,
   **Then** it says no citation is available for that rule.
4. **Given** the same determination, **When** its explanation is built twice, **Then** the two
   texts are identical.

### User Story 5 - Read the explanation of a decision (Priority: P2)

Caseworkers see each decision's explanation on the case page. Applicants see their past
applications and decisions for every coverage period, each with the explanation they were given
at the time.

**Why this priority**: Explanations only help if people can read them; this also shows the
system's transparency in the demo.

**Independent Test**: In the browser, open a determined case as a caseworker and check the stored
explanation and its citations; sign in as a returning demo applicant and check the decisions for
each coverage period.

**Acceptance Scenarios**:

1. **Given** a determined case, **When** the caseworker opens it, **Then** they see the
   caseworker explanation stored with the determination, with its citations, exactly as built
   at the time.
2. **Given** an applicant with past decisions, **When** they open their history, **Then** they see
   each coverage period's decision with its plain-language explanation as recorded at the time.

### Edge Cases

- A determination made under an earlier rule set version: its stored explanation is shown
  unchanged, with the manual version date it cited.
- A determination that could not evaluate a rule because information was missing: the
  explanation names the missing information for that rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-004-09**: The training-edition manual MUST be kept in the repository with its version
  date and a statement that it is a training edition. For the MVP it holds at least the
  sections the six eligibility rules (FR-003-01) cite.
- **FR-004-10**: For any determination, the system MUST build a plain-language explanation for
  applicants and a detailed one for caseworkers from a fixed template, stating the outcome,
  each rule's result and the values used, with a policy citation per rule. The applicant
  version covers the outcome and the rules that were not met; the caseworker version covers
  every rule. (Revised: no AI.)
- **FR-004-12**: Explanations MUST NOT change, contradict or soften the determination.
- **FR-004-13**: Each explanation MUST be stored with its determination as built at the time,
  so history shows the original explanation.
- **FR-004-15**: The case page (FR-001-27) MUST show each determination's caseworker explanation,
  with its citations, as stored at the time (FR-004-13). (Was FR-006-09, explanations part.)
- **FR-004-16**: Applicants MUST be able to see their past applications and decisions for every
  coverage period, each with its applicant explanation as recorded at the time. (Was FR-006-04.)
- **FR-004-18**: A citation table MUST map each eligibility rule to its manual section number,
  section title and manual version date. Explanations take their citations only from this
  table.
- **FR-004-19**: An explanation MUST be built only from the determination's values and the
  citation table, so the same determination always gives the same text. It is offered as
  `explain_determination(determination, audience) -> DecisionExplanation` and returns
  immediately.

### Deferred: 004b Policy search

Not in the MVP. If built later it is keyword search with no AI: FR-004-01 to FR-004-03,
FR-004-06 and FR-004-07 as written, and FR-004-04 limited to exact terms and section numbers.
US1 and US2 go with it.

### Removed

| ID | What it was |
|---|---|
| FR-004-04 (meaning half) | Matching by meaning (embeddings, reranking) |
| FR-004-05 | Relevance threshold tuned on an evaluation run |
| US3, FR-004-08, FR-004-14 | Retrieval and explanation evaluation sets and command |
| FR-004-11 | Automatic checks on AI-written explanations, and the "explanation review" task |
| FR-004-17 | Explanation runs in the AI activity section |
| SC-004-01, SC-004-03, SC-004-04 | Retrieval recall, off-topic rejection and search speed targets |

### Key Entities

- **Citation**: rule, section number, section title, manual version date.
- **Decision explanation**: determination reference, audience (applicant or caseworker), text,
  citations per rule, built time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-004-02**: 100% of citations in explanations carry section number, title and manual
  version date.
- **SC-004-05**: 100% of numbers in explanations match their determinations on the known-answer
  cases.
- **SC-004-06**: 100% of the six eligibility rules have an entry in the citation table. (Was
  95% of rules in generated explanations.)

## Assumptions

- The manual is a training edition written for this project and is synthetic like the rest of the
  data, so no terms-of-use limits apply. Every section carries a "training edition, not official
  policy" notice, and its values match the project values.
- There is one manual version.
