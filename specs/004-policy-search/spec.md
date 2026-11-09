# Feature Specification: Policy Search

**Feature Branch**: `feature/004-policy-search`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Search and citation of the Illinois Medicaid policy manual"

## Lane & Dependencies

- **Lane**: B (AI and knowledge)
- **Provides**: search over the Illinois policy manual returning cited passages. Used by 002
  (notice drafts), 005 (policy search tool) and 006 (explanations).
- **Depends on**: 000 (configuration).
- **Out of scope**: other states' manuals, non-medical chapters, answering general questions
  without citations, keeping the manual automatically up to date.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find relevant policy with citations (Priority: P1)

A component asks a question in plain language ("what counts as earned income?") and gets the
most relevant passages from the manual, each with its section number, title and source link.

**Why this priority**: Every explanation and notice must cite policy.

**Independent Test**: Run the evaluation questions and check the expected sections appear in the
top 5 results.

**Acceptance Scenarios**:

1. **Given** the indexed manual, **When** a question is asked, **Then** up to 5 passages are
   returned, each with section number, section title, source link and manual version date.
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

### Edge Cases

- A section is very long: it is split, and every part keeps its section number and title.
- Two sections are near-duplicates: both may be returned, each with its own citation.
- The manual is re-indexed: results and citations are the same for the same manual version.
- The question contains instructions aimed at the model: treated as a search query only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-004-01**: The system MUST index the medical eligibility chapters of the Illinois
  Department of Human Services policy manual, keeping section number, title, source link and
  manual version date for every passage.
- **FR-004-02**: Passages MUST follow the manual's own section structure; a split section MUST
  keep its section number and title on every part.
- **FR-004-03**: Search MUST return at most 5 passages, ranked by relevance, each with its
  citation.
- **FR-004-04**: Search MUST match both meaning and exact terms (section numbers, defined terms).
- **FR-004-05**: Search MUST return "no relevant policy found" when no passage meets the
  relevance threshold.
- **FR-004-06**: Search MUST accept a date and return only passages from the manual version in
  force on that date.
- **FR-004-07**: Indexing MUST be repeatable: the same manual version produces the same passages
  and citations.
- **FR-004-08**: An evaluation set of 30–50 questions with expected sections MUST exist, and an
  evaluation command MUST report top-5 recall and the average rank of the first correct section.
- **FR-004-09**: The manual's source, retrieval date, version date and terms of use MUST be
  recorded alongside the index.

### Key Entities

- **Policy passage**: text, section number, section title, source link, version date.
- **Search result**: question, date, ranked passages with citations, or "no relevant policy found".
- **Evaluation question**: question text and expected section(s).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-004-01**: The expected section appears in the top 5 results for at least 80% of
  evaluation questions.
- **SC-004-02**: 100% of returned passages carry a complete citation.
- **SC-004-03**: At least 90% of off-topic test questions return "no relevant policy found".
- **SC-004-04**: Search returns results in under 2 seconds on a team laptop.

## Assumptions

- The Illinois DHS policy manual is publicly available online with numbered sections. A team
  member confirms the current URL before Day 1. [NEEDS CLARIFICATION: Do the manual's terms of
  use allow saving a local copy for indexing, or must we index only pages fetched at run time?]
- Only one manual version will be available; date filtering is built for future versions.
- The 80% threshold is a starting target and can be revised after the first evaluation run.
