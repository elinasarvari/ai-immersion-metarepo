---
name: architecture-plan
description: Plan a feature as the architect - turn an approved spec into Spec Kit's plan artefacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) grounded in the existing code, rules and ADRs, make its significant decisions as ADRs, and write scope.json (lanes and repos). Use instead of a bare /speckit-plan when planning a Benefits Case feature, or when the user asks the architect to plan or design a feature.
---

# Architecture plan

You take on the **architect role**. Read `agents/architect/rules/behavior.md` and `agents/README.md` first; they bind you until step 6. Paths are from the metarepo root.

## 1. Inputs (read once, only these)
- `specs/<NNN-feature>/spec.md`: the feature (the folder the user named, or `.specify/feature.json`)
- `.specify/memory/constitution.md` and `project-rules/README.md` (the path → rules map), then only the rule files for the lanes the spec touches
- Earlier decisions on the same topics: `grep -rl "<keywords>" specs/*/decisions specs/*/research.md`
- The code that will change: `git -C repos/<repo> ls-files <area>`, then only the relevant modules

If the spec has open `[NEEDS CLARIFICATION]` markers, or a target repo isn't cloned, stop and report (behavior, section 6).

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

## 4. Self-check (scripts, not judgement)
```bash
python3 workflows/benefit-feature/scripts/wf.py plan-check <feature_dir>
python3 workflows/benefit-feature/scripts/wf.py decisions-check <feature_dir>
python3 workflows/benefit-feature/scripts/wf.py scope-check <feature_dir>
```
Fix anything they report before finishing.

## 5. Open items
If a person is present, ask the `Needs decision` questions and record answers as `architecture-decision` step 9 says. If unattended, leave them open; the workflow asks at its decision gate.

## 6. Report
≤10 lines: the files written, ADR counts by status, the open questions with recommendations, and the scope.
