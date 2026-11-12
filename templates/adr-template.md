# ADR-<NNN>-<nn>: <Short decision title>

- **Status:** Accepted | Accepted – auto-decided | Proposed – needs amendment | Needs decision | Superseded by ADR-…
- **Date:** YYYY-MM-DD
- **Feature:** specs/<NNN-feature>/ · **Requirements:** FR-…
- **Lanes affected:** Workflows | Agents | Knowledge & data | Platform & UI
- **Repos affected:** benefit-be | benefit-fe
- **Supersedes:** – (or ADR-…)

## Context

What has to be decided and why now. The forces in play: the requirements, rules (by ID), constitution principles, existing code (`repo:path:line`), earlier ADRs and constraints. 3–8 sentences.

## Options

### Option A: <name>
How it works in this codebase, in 2–4 sentences.
- **Pros:** …
- **Cons:** …

### Option B: <name>
…

### Option C: Do nothing / defer (when viable)
…

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Meets the spec (FR-…) | | | |
| Constitution and rules (IDs) | | | |
| Simplicity (constitution X) | | | |
| Security and privacy | | | |
| Testability | | | |
| Fits existing code and ADRs | | | |
| Reversibility | | | |
| Effort within the timeline | | | |

## Decision

We choose **Option …** because … (the deciding criteria, in 2–4 sentences).

For `Proposed – needs amendment`: the rule or principle, its current wording, the proposed wording, and the fallback option if the amendment isn't approved.

For `Needs decision`: the question, the options, and the recommendation, with the evidence someone who didn't plan the feature needs to decide it.

For `Accepted – auto-decided` (set only by the decision-maker agent), end with:
**Decided by:** decision-maker (automated), YYYY-MM-DD; architect recommended Option …
**Revisit if:** the observable condition that would make another option better

## Consequences

- **Good:** …
- **Bad / accepted trade-offs:** …
- **Work this creates:** per lane, per repo (feeds `/speckit-tasks`).

## How we verify it

Tests, contract tests, automated checks (for example an import-linter contract or a CI grep), or a spike that would show the decision is wrong. Name who checks: the compliance review, the code reviewer, or CI.

## References

Rule IDs, constitution principles, ADRs, docs and sources used.
