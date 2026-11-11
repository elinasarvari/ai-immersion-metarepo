---
name: architecture-plan
description: Plan a feature as the architect - turn an approved spec into Spec Kit's plan artefacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) grounded in the existing code, rules and ADRs, make its significant decisions as ADRs, and write scope.json (lanes and repos). Use instead of a bare /speckit-plan when planning a Benefits Case feature, or when the user asks the architect to plan or design a feature.
---

# Architecture plan

You are the **architect agent**. Read `agents/architect/architect.agent.md` and `agents/README.md` first; they bind you until step 7. Paths are from the metarepo root.

## 1. Inputs (read once, only these)
- `specs/<NNN-feature>/spec.md`: the feature (the folder the user named, or `.specify/feature.json`)
- `.specify/memory/constitution.md` and `project-rules/README.md` (the path → rules map), then only the rule files for the lanes the spec touches
- Earlier decisions on the same topics: `grep -rl "<keywords>" specs/*/decisions specs/*/research.md`
- The code that will change: `git -C repos/<repo> ls-files <area>`, then only the relevant modules
- What other features already define for the same things (collections, migrations, API routes, contracts, workers): `origin/main` in each target repo, and the other specs' `data-model.md` and `contracts/` (`grep -rl "<collection or route>" specs/*/data-model.md specs/*/contracts`). Reuse a definition that exists, with its names and fields, rather than defining it again. If a feature in progress defines the same thing differently, record which feature owns it in an ADR, so the two don't clash at merge (the integrator agent resolves what still does: main wins).

If the spec has open `[NEEDS CLARIFICATION]` markers, or a target repo isn't cloned, stop and report (agent file, section 6).

## 2. Plan (Spec Kit's plan, done as architect)
Follow `skills/speckit-plan/SKILL.md` (its setup script, template, Phase 0 and Phase 1), with these additions:
- **Technical Context and Project Structure:** the real stack and folders from `project-rules/backend-architecture.md` and `frontend-ui.md`, and the target repos as `repos/benefit-be` / `repos/benefit-fe`.
- **Constitution Check:** each principle I–X, pass or the ADR that handles it.
- **research.md:** the smaller choices (decision, reason, alternatives), dated.
- **data-model.md / contracts/:** `packages/domain` models, API endpoints (OpenAPI), signals and MCP tools that cross lanes or repos. These become the `[contracts]` tasks.
- Add **"Architecture decisions"** (each ADR by ID and status) and **"Contracts between lanes"** sections to `plan.md`.

For the significant decisions found along the way, use the `architecture-decision` skill, steps 1–8, in this same session, and reference the ADRs from the plan. Use `agents/architect/skills/architecture-capabilities/SKILL.md` only for the areas a decision touches.

## 3. Scope
Write `specs/<NNN-feature>/scope.json`:
```json
{"lanes": ["data-lane", "platform-ui-lane"], "repos": ["benefit-be", "benefit-fe"], "reason": "<one line per lane>"}
```
Lanes: `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane` (ownership in `project-rules/backend-architecture.md`). Include a lane only if the plan changes its folders.

## 4. Brief the next agents
Write `specs/<NNN-feature>/brief.md`, at most a page. The decision-maker and the spectator read it first and open the sources only where they need more, so it saves them re-reading what you already read:
```markdown
# Brief: <NNN-feature>
## Requirements
- FR-…: <one line> (acceptance scenarios: US1-AS1, …)
## Rules that apply
- <rule ID>: <why it applies here>
## Code touched
- repos/<repo>:<path>: <what changes> (lane)
## Existing tests nearby
- repos/<repo>:<test path>: <what it covers>
## Open decisions
- ADR-…: <question> → Recommendation: <option> (the plan assumes it)
```
Facts only, each with its source, as everywhere else (agent file, section 4).

## 5. Self-check (a script, not judgement)
```bash
python3 workflows/benefit-feature/scripts/wf.py plan-gate <feature_dir>   # plan.md, ADRs, scope.json and brief.md
```
Fix anything it reports before finishing. The workflow runs the same gate after this step and stops on a failure.

## 6. Open items
Leave every `Needs decision` and `Proposed – needs amendment` ADR open, with its options and your recommendation; the plan assumes the recommendation. They're settled separately: in a workflow run by the decision-maker agent; in chat, ask the user, or run the decision-maker agent if they say to decide for them (`architecture-decision` step 9).

## 7. Report
≤10 lines: the files written, ADR counts by status, the open questions with recommendations, and the scope. The spectator plans the tests next, from the plan as decided.
