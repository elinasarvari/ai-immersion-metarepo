# Feature Specification: Policy Search and Decision Explanations

**Feature Branch**: `feature/004-policy-search`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Search and citation of the Illinois Medicaid policy manual, and plain-language explanations of decisions"

## Lane & Dependencies

- **Lane**: B (AI and knowledge)
- **Provides**: search over the Illinois policy manual returning cited passages, and plain-language
  explanations of determinations. Used by 001 (explanations requested after each
  determination), 002 (notice drafts), 005 (policy search tool) and 006 (shows stored
  explanations).
- **Depends on**: 000 (configuration, AI provider), 003 (determinations and rule traces; stubbed
  until ready).
- **Out of scope**: other states' manuals, non-medical chapters, answering general questions
  without citations, keeping the manual automatically up to date, changing or overriding any
  determination.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find relevant policy with citations (Priority: P1)

A component asks a question in plain language ("what counts as earned income?") and gets the
most relevant passages from the manual, each with its section number, title and source link.

**Why this priority**: Every explanation and notice must cite policy.

**Independent Test**: Run the evaluation questions and check the expected sections appear in the
top 5 results.

**Acceptance Scenarios**:

1. **Given** the indexed manual, **When** a question is asked, **Then** up to 5 passages are
   returned, each with section number, section title and manual version date.
2. **Given** a question using an exact section number or a term of art, **When** it is asked,
   **Then** the matching section is returned first.

---

### User Story 2 - Say when nothing relevant is found (Priority: P1)

If no passage is relevant enough, the search says so instead of returning weak matches.

**Why this priority**: Prevents explanations built on irrelevant policy.

**Independent Test**: Ask off-topic questions and confirm "no relevant policy found".

**Acceptance Scenarios**:

1. **Given** a question unrelated to the manual, **When** it is asked, **Then** the result is "no
   relevant policy found" with no passages.

---

### User Story 3 - Measure retrieval quality (Priority: P2)

The team can measure how well search finds the right sections and see if a change made it
better or worse.

**Why this priority**: Turns "it seems to work" into a number for the demo.

**Independent Test**: Run the evaluation command and get recall and ranking scores.

**Acceptance Scenarios**:

1. **Given** the evaluation set, **When** the evaluation runs, **Then** it reports the share of
   questions whose expected section is in the top 5, and the average rank of the first correct
   section.

---

### User Story 4 - Explain a decision in plain language (Priority: P1)

For any determination, the applicant and the caseworker can read a plain-language explanation of
the outcome: what each rule found, the values used, and the policy section behind each rule.

**Why this priority**: "Why was this decided?" is central to the demo and to trust in the system.

**Independent Test**: Generate explanations for the known-answer determinations and check every
number matches the determination and every rule has a citation.

**Acceptance Scenarios**:

1. **Given** an income-ineligible determination, **When** its explanation is generated, **Then** it
   states the outcome, the household income, size and limit used, and cites the policy section
   for the income rule.
2. **Given** any determination, **When** its explanation is generated, **Then** every number in it
   matches the determination exactly and nothing is stated that the determination or the cited
   passages do not support.
3. **Given** a rule with no supporting passage found, **When** the explanation is generated,
   **Then** it says no citation is available for that rule and the explanation is marked for
   caseworker review.

### Edge Cases

- A section is very long: it is split, and every part keeps its section number and title.
- Two sections are near-duplicates: both may be returned, each with its own citation.
- The manual is re-indexed: results and citations are the same for the same manual version.
- The question contains instructions aimed at the model: treated as a search query only.
- The AI provider is unavailable when an explanation is needed: the rule-by-rule trace is shown
  without the plain-language summary, and the explanation is generated later (FR-001-14).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-004-01**: The system MUST index the project's training-edition Illinois Medicaid policy
  manual, keeping section number, title and manual version date for every passage.
- **FR-004-02**: Passages MUST follow the manual's own section structure; a split section MUST
  keep its section number and title on every part.
- **FR-004-03**: Search MUST return at most 5 passages, ranked by relevance, each with its
  citation.
- **FR-004-04**: Search MUST match both meaning and exact terms (section numbers, defined terms).
- **FR-004-05**: Search MUST return "no relevant policy found" when no passage meets the
  relevance threshold. The threshold is set in configuration during the first evaluation run so
  that SC-004-03 is met.
- **FR-004-06**: Every result MUST include the version date of the manual it came from (there is
  one manual version).
- **FR-004-07**: Indexing MUST be repeatable: the same manual version produces the same passages
  and citations.
- **FR-004-08**: An evaluation set of 30–50 questions with expected sections MUST exist, and an
  evaluation command MUST report top-5 recall and the average rank of the first correct section.
- **FR-004-09**: The manual's version date and a statement that it is a training edition MUST be
  recorded alongside the index.
- **FR-004-10**: For any determination, the system MUST produce a plain-language explanation for
  applicants and a detailed one for caseworkers, stating the outcome, each rule's result and the
  values used, with a policy citation per rule.
- **FR-004-11**: Every number in an explanation MUST match the determination exactly, checked
  automatically, and every statement MUST refer to a rule in the determination or a returned
  passage. An explanation that fails these checks MUST be rejected and marked for review.
- **FR-004-12**: Explanations MUST NOT change, contradict or soften the determination.
- **FR-004-13**: Each explanation MUST be stored with its determination as generated at the time,
  so history shows the original explanation.

### Key Entities

- **Policy passage**: text, section number, section title, version date.
- **Search result**: question, date, ranked passages with citations, or "no relevant policy found".
- **Evaluation question**: question text and expected section(s).
- **Decision explanation**: determination reference, audience (applicant or caseworker), text,
  citations per rule, generated time, model used.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-004-01**: The expected section appears in the top 5 results for at least 80% of
  evaluation questions.
- **SC-004-02**: 100% of returned passages carry a complete citation.
- **SC-004-03**: At least 90% of off-topic test questions return "no relevant policy found".
- **SC-004-04**: Search returns results in under 2 seconds on a team laptop.
- **SC-004-05**: 100% of numbers in generated explanations match their determinations on the
  known-answer cases.
- **SC-004-06**: At least 95% of rules in generated explanations carry a policy citation.

## Assumptions

- The manual is a training edition written for this project and is synthetic like the rest of the
  data, so no terms-of-use limits apply.
- There is one manual version, so search does not filter by date.
- The team writes the training-edition manual (AI-assisted), modelled on the structure of the
  Illinois Department of Human Services policy manual: 25–40 numbered sections covering the six
  eligibility rules (FR-003-01), income counting, verification, application timeliness, requests
  for information and redeterminations. Every section carries a "training edition, not official
  policy" notice, and its values match the project values.
- The 80% threshold is a starting target and can be revised after the first evaluation run.
