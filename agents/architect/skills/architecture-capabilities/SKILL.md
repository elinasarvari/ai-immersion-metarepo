---
name: architecture-capabilities
description: The software-engineering areas the architect covers for the Benefits Case project (contracts and domain modelling, API design and versioning, data and storage, Temporal orchestration, AI agents, retrieval, security and privacy, frontend architecture, testing strategy, operability, dependencies, cross-repo delivery), with the questions to answer, the practices that apply in this stack, and red flags. Use when making or reviewing an architecture decision, or when asked what good practice is for one of these areas in benefit-be or benefit-fe.
---

# Architecture capabilities

This skill is part of the architect role (`agents/architect/`). It sets out **what** to examine in each area. **How** a decision is made is in the `architecture-decision` skill (`agents/architect/skills/architecture-decision/SKILL.md`); the role's limits are in `agents/architect/rules/behavior.md`. All paths here are from the metarepo root. You can also use it on its own, for example to check a design or answer "what's good practice for X here".

Use it to make an ADR's options complete and its comparison honest. For each area a decision touches, answer its questions in the ADR's Context or Options. Treat every red flag you see as something the decision must resolve, or explicitly accept with a reason.

Rule IDs refer to `project-rules/`; roman numerals to the constitution. Rules win over anything in this file; if they disagree, follow the rule and flag the gap.

---

## 1. Domain modelling and contracts

**Questions:** Which data crosses a lane or repo boundary? Who owns each model? Is it a command, an event, a query result or a stored record? What happens to old data and running workflows when it changes?

**Practice here:**
- Shared models live in `packages/domain` as Pydantic v2 models (BA-6, BA-8). Agree contracts first (VI).
- Prefer additive, backward-compatible changes (new optional fields). Renames and removals need a migration plan.
- Separate API models from storage models when their lifecycles differ.

**Red flags:** dicts passed between lanes; a lane importing another lane's internals; one model reused for API, storage and workflow payloads "for convenience"; changing a signal payload used by running workflows.

## 2. API design and versioning

**Questions:** Is it a resource or an action? Who calls it (which role)? Is it idempotent? What do errors look like? Does it change the OpenAPI contract with `benefit-fe`?

**Practice here:**
- `/api/v1`, FastAPI and Pydantic v2 (PL-1). The API starts workflows and sends signals; it never calls agents, rules or RAG directly (PL-2).
- Breaking changes get a new version path (PL-4). OpenAPI changes are paired with a `benefit-fe` PR (PL-3, FE-3).
- One error format (spec 000, R11). Pagination for lists. Idempotency keys or workflow-ID idempotency for actions that start work.

**Red flags:** business logic in routers (BA-2); an endpoint that waits synchronously for an agent or workflow to finish; returning storage models directly; unversioned breaking changes.

## 3. Data and storage

**Questions:** Which collection, in `benefit` or `benefit_audit` (KD-9)? Is it household-scoped? What are the access patterns, indexes and volume? Which writes must be atomic? How is it migrated and rolled back? Is it audit-relevant?

**Practice here:**
- MongoDB is the only operational database. PyMongo async through repository modules only (KD-9, KD-10, `database.md`).
- Household-scoped documents carry `household_id` (and `case_id`), and every query filters on it (KD-9).
- Multi-document writes (a case change plus its audit entry, an outbox record) use a transaction (KD-10).
- Collection, validator and index changes go through versioned migrations with downgrades (KD-11). The audit log is append-only, under a restricted role (KD-12).
- Analytics reads pseudonymised exports in DuckDB, never the live database (KD-15).

**Red flags:** queries built outside repository modules; a query without the household filter; multi-document changes without a transaction; schema or index changes outside migrations; unbounded queries; personal data in exports.

## 4. Workflow orchestration (Temporal)

**Questions:** What's durable state, and what's an activity? Where are the human waits and deadlines? What's the workflow ID (idempotency)? How does this change affect workflows already running?

**Practice here:**
- Workflows deterministic, side effects only in activities (TW-1, TW-2). Human review as durable waits with timers (TW-4, TW-8).
- One `CaseWorkflow` per case, with the ID derived from the case or household (TW-3, TW-6). Signals for actions, queries for reads (TW-5).
- Change running workflows with `workflow.patched()` or a new type (TW-7). Activities thin, idempotent, with timeouts and retries (TW-9 to TW-11).

**Red flags:** I/O or clocks in workflow code; waiting inside an activity or agent; large payloads in workflow history (store a reference instead); a new workflow when a signal on the existing one would do.

## 5. AI agents and LLM use

**Questions:** What decision does the AI support, and who makes it? What does it cite? What happens on low confidence, a parse failure or a provider outage? How is quality measured?

**Practice here:**
- Rules decide; AI assists (I, PR-1, AG-12). Every output cited (III, PR-2, AG-11). Structured output via JSON schema, no forced tool choice, no temperature or top_p (AG-6, AG-7, AG-10).
- One graph per agent with a bounded retry, then escalation (AG-3). External access only via MCP or `packages/rag` (AG-4). Provider chosen in one factory (AG-5).
- Prompts versioned (AG-13). Untrusted text delimited (AG-14). Evals with thresholds (AG-17). Overrides feed the eval set (AG-18).

**Red flags:** an agent whose output directly changes a determination; free-text parsing; prompt text built from user input; a new agent where a rule or a deterministic function would do (X).

## 6. Retrieval (RAG)

**Questions:** What's the corpus and how is it chunked? What citation does a chunk carry? How is retrieval quality measured, and what's the threshold?

**Practice here:** Qwen3 embeddings with a query prefix (KD-4); in-application hybrid search (cosine over cached embeddings plus BM25, rank-fused), top 40 → rerank → top 5, no vector index (KD-5); stable chunk IDs and source metadata (KD-6); models loaded once (KD-7); retrieval evals on every change (KD-8).

**Red flags:** chunk IDs that change on re-ingest (breaking citations); changing chunking or embeddings without re-running evals; retrieval inside workflow code.

## 7. Security and privacy

**Questions:** Who can do this (role and household)? Where is it enforced? What does it log? What's the trust level of each input? What happens if a token or credential leaks?

**Practice here:**
- JWT roles enforced in the API and every MCP tool, plus case access (PL-5, PL-6), with rejection tests (PL-7). MCP tools accept only the worker's case-scoped credential (PL-6, FR-000-22).
- Synthetic data only (PR-3, VIII). No PII in logs (PL-11). Secrets via `.env` (`security.md`).
- Use OWASP ASVS as the checklist for auth, session, input validation and error handling.

**Red flags:** an authorization check only in the UI (FE-6); a tool reachable with a user session; logging documents or prompts with personal data; a new endpoint without role tests.

## 8. Frontend architecture (benefit-fe)

**Questions:** Which area is it (caseworker console or applicant portal)? What server state does it read and change? How are loading, empty and error states handled? How is AI content shown?

**Practice here:** generated OpenAPI client only (FE-3); TanStack Query for server state, with keys that include the case ID (FE-4, FE-5); role-guarded routes (FE-6); AI content labelled, cited and overridable (FE-7); shadcn/ui and WCAG 2.1 AA (FE-9); all states handled (FE-10).

**Red flags:** hand-written API types; server data copied into local state; computing metrics or eligibility in the browser (FE-8, PR-1); AI output styled like a decision.

## 9. Testing strategy and fitness functions

**Questions:** Which test level proves each requirement (unit, integration, contract, workflow time-skipping and replay, end-to-end, eval)? What automated check would catch a violation of this decision later?

**Practice here:** test-first (V, `testing.md`); test names carry the `FR-…` ID (spec 009, FR-009-04); no live model in CI (FR-000-20); the workflow replay test for every workflow change (TW-14).

**Fitness functions:** turn decisions into checks wherever possible, for example:
- an import-linter contract for BA-3 to BA-7
- a CI grep for `temporalio` in `packages/agents` (AG-2)
- an OpenAPI drift check (spec 000, R18)
- a schema test for `packages/domain` compatibility

**Red flags:** a decision whose only safeguard is code review; tests that call the live model; requirements without a named test.

## 10. Operability and observability

**Questions:** Which process does it run in? How does it start (`make dev`, Procfile)? How do you see what it did (logs, traces, audit log)? What happens on failure and restart?

**Practice here:** native on a Mac, no Docker (PR-5, IX); every process in the Procfile (PL-12); structlog JSON with `case_id` and `workflow_id` (PL-11, TW-17); Phoenix tracing for AI runs (AG-15); timeouts and retries on external calls (`security.md`); fail-fast settings (spec 000, R7).

**Red flags:** a new long-running process not in the Procfile; a background thread in the API; failures that are only visible in a terminal; no way to reproduce the demo state (spec 009, FR-009-08).

## 11. Dependencies and build vs buy

**Questions:** Is a new dependency needed at all (X)? Is it maintained, licensed suitably, and does it run natively on a Mac? What does it cost to remove later?

**Practice here:**
- Pin the exact version and commit lockfiles (PR-4).
- Check the latest release, maintenance activity and licence, and date the check.
- Prefer the standard library or something already in the stack. State the reason in `plan.md` (X).

**Red flags:** a framework added for one function; a service needing Docker or a cloud account; overlapping libraries (two HTTP clients, two validation libraries).

## 12. Cross-repo delivery and change sequencing

**Questions:** Which repos and lanes change, and in what order? What can merge independently? What breaks if one PR merges and the other doesn't?

**Practice here:**
- Contracts first (VI, BA-8). The `benefit-be` PR opens before `benefit-fe` when OpenAPI changes (PL-3).
- The same branch name in both repos, with linked PRs.
- Each lane's files change in their own commits (BA ownership).
- Scope cuts come from the agreed fallback list, not by skipping tests (X).

**Red flags:** a frontend change that only works with an unmerged backend; a contract change hidden inside a feature PR; one task that edits several lanes' folders.
