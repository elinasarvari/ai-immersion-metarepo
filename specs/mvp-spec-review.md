# MVP spec review: no-AI scope, 3-hour build

Reviewed 2026-11-11 against `specs/*/spec.md` on `feature/new-agent-refactor` and the code on `main` of `benefit-be` and `benefit-fe`. Effort figures are estimates, in person-hours, for one developer with Copilot.

## Executive summary

Of the seven specs listed, two need no work: 006 was retired on 2026-11-10 (its screens moved into the other features) and 005 exists only to serve AI agents, so it is retired with them. 009 is not missing: it is the delivery factory in the metarepo, not a product feature. That leaves five specs to build: 002, 004, 007, 008 and 011. With every AI component removed they come to about 10.5 person-hours. **Four people can finish all five in 3 hours with no slack. Three people (the current team) cannot: defer 008 and the policy search half of 004.** All five can start at hour 0 after a 20-minute contract session, because everything they need from 000, 001, 003 and 010 is already on `main`. The one real sequence is 011 → 007, and 007 is the highest-risk spec.

The line counts in the request are out of date. Actual counts are used below.

## Spec analyses

### 002 - Document Verification

#### Current State
- **Lines of Code:** 254
- **AI/LLM Usage:** Yes. The whole feature: LLM extraction with confidence scores, re-extraction, the 3-loop self-check, AI-drafted requests for information, the agent evaluation set, AI activity on the case page, prompt-injection handling.
- **Complexity:** High
- **Status:** Needs Simplification (a rewrite: about 14 of 20 requirements go)

#### Dependencies
- **Depends On:** 001 (application form, case page), 003 (monthly income formula FR-003-18, synthetic pay stubs), 010 ("Verification review" reason). All on `main`.
- **Blocks:** 011 and 007 reuse its upload component in their response forms (soft: they ship "confirm details" first and add upload at integration).
- **Parallelizable With:** 004, 007, 008, 011

#### MVP Simplification
- **Remove:** extraction, confidence and re-extraction (FR-002-01, -02); verification loops (-04); AI drafts (-05, -12); citation checks (-06); injection handling (-07); run records, evaluation set and overrides-as-eval-data (-09, -10, -11, -19); simulated source checks (-13); AI activity (-20). US1, US3, US4 and most of US6.
- **Keep:** pay stub upload with limits (FR-002-17). The applicant types each stub's employer, pay frequency, gross pay and pay date. The system converts to monthly income and records a finding when it differs from declared income by more than 10% (FR-002-03), when the stub is older than 45 days or a job has no stub (FR-002-15), or when the name matches no household member (FR-002-14). Any finding raises a "Verification review" task. The case page lists documents, entered values and findings (FR-002-18). The caseworker can correct a value or dismiss a finding with a reason.
- **Expected LOC After:** 190 as rewritten (about 110 of requirements; the rest is the removed-items table and stories)
- **Recommended Changes:**
  - Rename to "Pay stub upload and income check". `verify_documents(case_id) -> VerificationResult` stays as the interface, minus the tool credential, so 001's workflow doesn't change.
  - It must set "identity verified" for the rules (see hidden dependencies): a plain name and date-of-birth lookup against the seed data.

#### Staffing & Timing
- **Estimated Effort:** 2-3 hours (about 2)
- **Team Capacity:** 1 person
- **Start After:** Immediately

---

### 004 - Policy Search and Decision Explanations

#### Current State
- **Lines of Code:** 206
- **AI/LLM Usage:** Yes. Meaning-based search (embeddings, reranking; `packages/rag/` already has both), LLM-written explanations, automatic checks on LLM output, retrieval and explanation evaluations.
- **Complexity:** Medium
- **Status:** Can be Decomposed (two unrelated halves)

#### Dependencies
- **Depends On:** 003 (rule-by-rule trace FR-003-05, on `main`), 001 (case page)
- **Blocks:** 011's denial notice includes the applicant explanation (soft: the spec already allows the rule trace as fallback)
- **Parallelizable With:** 002, 007, 008, 011

#### MVP Simplification
- **Remove:** meaning-based search (FR-004-04, meaning half), relevance threshold tuning (-05), both evaluation sets (-08, -14), LLM output checks and "explanation review" (-11), AI activity (-17), the two-audience LLM generation in -10.
- **Keep:** explanations rendered from a fixed template over the 003 rule trace, with a static table mapping each of the six rules to its manual section. Since the text is built from the determination, numbers match by construction. Stored with the determination (-13), shown on the case page (-15) and in the applicant's history (-16).
- **Expected LOC After:** 146 as rewritten, explanations only
- **Recommended Changes:**
  - Split it. 004a "Decision explanations" is MVP. 004b "Policy search" becomes keyword and section-number matching over the manual, but with the agents gone nothing calls it. Build it last or not at all.
  - Cut the manual to the sections the six rules cite.

#### Staffing & Timing
- **Estimated Effort:** 1-2 hours (1 for explanations, 0.5-1 more for keyword search)
- **Team Capacity:** 1 person
- **Start After:** Immediately

---

### 005 - Agent Tool Access

#### Current State
- **Lines of Code:** 150
- **AI/LLM Usage:** Yes. All of it: 11 tools for AI agents, case-scoped credentials, tool-call audit.
- **Complexity:** Medium
- **Status:** Retire. Nothing calls tools once the agents are gone.

#### Dependencies
- **Depends On:** n/a
- **Blocks:** None after retirement. 002 (FR-002-13) and 007 (FR-007-13) referenced its simulated sources; both references are removed.
- **Parallelizable With:** n/a

#### MVP Simplification
- **Remove:** every requirement, including simulated latency and failures (FR-005-07).
- **Keep:** only the idea behind FR-005-12, as one function owned by 002: look up a person's identity match and per-job income in the seed data. No delays, no failures, no credential.
- **Expected LOC After:** 29 (a "retired" note like 006's)
- **Recommended Changes:** retire the spec; leave the unused `tool_calls` and `agent_runs` collections in the baseline migration alone.

#### Staffing & Timing
- **Estimated Effort:** none (10 minutes for the retirement note)
- **Team Capacity:** none
- **Start After:** n/a

---

### 006 - Caseworker & Applicant Portal

#### Current State
- **Lines of Code:** 58 (a mapping table, not 195 lines of requirements)
- **AI/LLM Usage:** No
- **Complexity:** Low
- **Status:** Already retired on 2026-11-10. Its screens live in 001, 002, 004, 007, 010 and 011; its shared rules are FR-000-29 to -31.

#### Dependencies
- **Depends On:** None. **Blocks:** None. **Parallelizable With:** n/a

#### MVP Simplification
- **Remove:** nothing. **Keep:** the ID mapping table.
- **Expected LOC After:** 58
- **Recommended Changes:** update three rows that point to removed requirements (FR-006-02 → 002's correct-or-dismiss action; FR-006-14 AI activity → removed).

#### Staffing & Timing
- **Estimated Effort:** none
- **Team Capacity:** none
- **Start After:** n/a

---

### 007 - Redeterminations

#### Current State
- **Lines of Code:** 229
- **AI/LLM Usage:** Partly. The renewal form is AI-drafted (FR-007-03 via FR-002-12), and the renewal check re-verifies through the agent tool sources (FR-007-13).
- **Complexity:** High. A second path through the Temporal case workflow, a daily schedule, coverage period states, and three screens.
- **Status:** Needs Simplification, and can be decomposed

#### Dependencies
- **Depends On:** 001, 003, 010 (on `main`); 011 (notice types, the wait-with-deadline pattern, demo clock); 002 (upload component, income check)
- **Blocks:** 008's automatic renewal rate, at run time only (008 builds against seeded history)
- **Parallelizable With:** 002, 004, 008. With 011 only if the notice and timer contract is fixed first.

#### MVP Simplification
- **Remove:** the AI-drafted form (replaced by a form generated from the list of missing or out-of-date items); simulated sources (FR-007-13 keeps its meaning but reads identity and income from the plain seed-data lookup that 002 now owns, FR-002-22).
- **Keep:** start on demand from the household page (FR-007-10, -18); automatic renewal on held data with a template notice (-02, -05, -14); the form, a 30-day wait and a review task on no response (-03, -04); coverage never ends automatically (-04, -06); one per period (-07).
- **Expected LOC After:** 221 as rewritten (stories kept in full; deferred parts listed)
- **Recommended Changes:**
  - Split it. 007a: on-demand start, automatic renewal, no-response review (US1, US3, US6). 007b: the applicant's response form (US2, US5). Build 007a first; 007b only if 011 has landed.
  - Defer the daily schedule (FR-007-01) and the upcoming page (US4, FR-007-09, -17). The demo uses the button, and the README already lists US4 as the first cut.

#### Staffing & Timing
- **Estimated Effort:** > 3 hours as written; 2-3 hours for 007a plus a thin 007b
- **Team Capacity:** 1 person, plus help in the last 45 minutes
- **Start After:** Immediately against the agreed contract; integrate after 011

---

### 008 - Program Metrics

#### Current State
- **Lines of Code:** 152
- **AI/LLM Usage:** No AI components. One metric measures AI (AI override rate), and US1 is justified by "show the AI is helping".
- **Complexity:** Medium, mostly from the separate reporting store (DuckDB and dbt in `analytics/`), pseudonymous keys and scheduled refresh.
- **Status:** Needs Simplification

#### Dependencies
- **Depends On:** 001, 003, 010 (on `main`). 003's seed data includes historical decisions and redetermination outcomes with expected metric values, so it needs neither 007 nor 011 to build and test.
- **Blocks:** None
- **Parallelizable With:** all

#### MVP Simplification
- **Remove:** AI override rate. Defer: the reporting store and pseudonymous keys (FR-008-02), scheduled refresh and failed-refresh handling (-01, -05), US3 and US4.
- **Keep:** four metrics computed on request from the operational data: average time to decision, decided within deadline, automatic renewal rate, procedural denial rate. Month filter, "no data" handling (-06), staff-only access (-07), expected values on seed data (-04).
- **Expected LOC After:** 128 as rewritten
- **Recommended Changes:**
  - One read-only endpoint and one page. With no copy of the data there is no personal data to scrub and nothing to refresh.
  - If the team wants a fifth metric, "caseworker override rate" on adverse determinations (010) replaces the AI one.

#### Staffing & Timing
- **Estimated Effort:** 1-2 hours (about 1.5)
- **Team Capacity:** 1 person
- **Start After:** Immediately

---

### 011 - Applicant Waits & Notices

#### Current State
- **Lines of Code:** 248
- **AI/LLM Usage:** Partly. Two of seven notice types are AI-drafted (FR-011-06), and FR-011-07 requests LLM explanations with retries and a fallback.
- **Complexity:** Medium to High. Workflow waits and timers, the demo clock, notice approval, three screens.
- **Status:** Needs Simplification. Nothing of it is built yet: the API has routes only for auth, applications and cases.

#### Dependencies
- **Depends On:** 001, 010 (on `main`). Soft: 002 (upload in the response form), 004 (explanation text in the denial notice; the rule trace until it lands)
- **Blocks:** 007 (notices, wait pattern, demo clock)
- **Parallelizable With:** 002, 004, 008; 007 with the contract fixed

#### MVP Simplification
- **Remove:** AI drafts. All seven notices come from fixed templates; the request for information is filled from 002's findings. FR-011-07 becomes: render the explanation when the determination is stored (no retries, no provider outage cases). SC-011-04 goes.
- **Keep:** the 15-day wait and missed-deadline review task (FR-011-01 to -03); the demo time scale and "Advance clock" (-04, -05, -11); caseworker approval of adverse notices and requests for information (-08); the applicant's notice list and response (-09, -10).
- **Expected LOC After:** 263 as rewritten (six stories kept; AI parts replaced, not dropped)
- **Recommended Changes:**
  - Drop "edit and approve" with two stored versions (FR-011-08): template notices need approve or reject only.
  - Publish the notice type list, timer names and the applicant-response signal in the first 20 minutes, because 007 builds on them.

#### Staffing & Timing
- **Estimated Effort:** 2-3 hours (about 2.5)
- **Team Capacity:** 1 person; a second on its screens if available
- **Start After:** Immediately

## Parallelization plan

| Phase | When | Work | People busy |
|---|---|---|---|
| 0. Contracts | 0:00-0:20 | Everyone together: notice types and templates, timer names, `verify_documents` and `explain_determination` signatures without credentials, where "identity verified" comes from, who edits the case workflow file | all |
| 1. Build | 0:20-2:15 | 002, 011, 007a, and (fourth person) 008 then 004a | 3-4 |
| 2. Integrate | 2:15-3:00 | 007 onto 011's notices and timers; upload into the 011 and 007 response forms; explanation text into the denial notice; one end-to-end demo run | all |

```
Phase 1 (Hour 0:20): Start Immediately (Independent)
  - 002, 004a, 008, 011
  - 007a (against the Phase 0 contract)

Phase 2 (Hour 2:15): Start After Phase 1
  - 007b and 007's integration with 011
  - 004b keyword search (only if time remains)

Critical Path (Longest Dependency Chain):
  - Contracts → 011 → 007 → end-to-end demo
  - Est. Duration: 3 hours, no slack

Total Specs Parallelizable: 5 of 5 that still need building (005 and 006 need none)
Estimated Total Effort: about 10.5 person-hours; 3 hours with 4 people
```

## Dependency graph

```
On main: 000, 001, 003, 010
   │
   ├── 002 income check ──(upload component)──┐
   ├── 004a explanations ──(notice text)──┐   │
   ├── 011 waits & notices ◄──────────────┘   │
   │        │                                 │
   │        └──► 007 redeterminations ◄───────┘
   └── 008 metrics (seed data only; reads 007 outcomes at run time)

Solid dependency: 011 → 007. Everything else is soft (stub or fallback exists).
```

## Risks and recommendations

- **Shared files will conflict.** 002, 011 and 007 all change the one case workflow (`apps/worker/workflows/case.py`), and 002, 004, 011 and 007 all add sections to the same case page in `benefit-fe`. Name one owner for the workflow file (the 011 person) and have the others add activities and page sections in their own files.
- **The "stable" specs still describe AI.** 010's review reasons table includes "Notice approval: an AI-drafted notice", "Explanation review" and AI causes for "Verification review"; 000 requires AI provider selection, agent credentials and AI tracing (FR-000-12, -22, -28). Leave the code alone, mark those requirements "not in MVP", and trim 010's table in Phase 0.
- **Rule sets and CI may require AI gates.** I did not check the constitution or CI for evaluation gates. If they exist, switching them off is a rule change that needs all three team members.
- **No slack.** If Phase 1 runs late, cut in this order: 004b, 007b, 008's month filter, 008 entirely.

## Answers to the five questions

**1. Can all seven be completed in 3 hours?** Two need no build (005 retired, 006 already retired). The other five: yes with four people, no with three.
- Four people: A on 011; B on 007; C on 002, then upload integration; D on 008, then 004a.
- Three people: A on 011, B on 007a, C on 002 then 004a. Defer 008 and 004b.
- Two people: 002 and 011 plus 004a. Defer 007 and 008.

**2. Dependency order.** Contracts → {002, 004a, 008, 011, 007a in parallel} → 007 integration → demo. The only strict sequence is 011 → 007.

**3. Merge or split.**
- Retire 005; its one surviving function (seed-data identity and income lookup) moves into 002.
- Split 004 into 004a explanations (MVP) and 004b keyword policy search (last or dropped).
- Split 007 into 007a automatic renewal and 007b applicant response.
- Move the request-for-information text from 002 into 011's templates, so 011 owns all seven notices.
- 006 stays retired. 009 is the delivery factory, not a product spec.

**4. Hidden dependencies.**
- 003's rules need "identity verified" and documented monthly income, which today come from 005's sources through 002 (FR-003-01, FR-002-13). After the cuts, 002 must supply both or every case fails the identity rule.
- 008's automatic renewal rate and 007's on-demand renewals depend on 003's seed data having coverage periods and historical outcomes.
- The shared workflow file and case page, and 010's review reasons table (see risks).
- 007's 30-day wait reuses 011's wait and demo clock; without 011 it can't be demonstrated.

**5. Highest-risk spec.** 007. It has the most dependencies (001, 003, 010, 011, 002), changes long-running workflow code that three specs touch, and is over 3 hours as written. 002 has the most rewriting but is low risk once it is manual entry plus arithmetic.
