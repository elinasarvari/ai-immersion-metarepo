---
name: feature-workflow
description: Run the full feature workflow for the Benefits Case project (benefit-be / benefit-fe): Spec Kit specify, plan with the lane agents, tasks, implement, rules gate with lane-agent reviews, checks and evals, then PRs. Use when the user asks to build, deliver or ship a feature end to end, or asks what the next step is.
---

# Feature workflow

Follow [workflows/feature.md](../../workflows/feature.md) step by step.

- At the start, find where the feature is: check `specs/` for its folder and which of `spec.md`, `plan.md` and `tasks.md` exist, and the branch state in `repos/benefit-be` and `repos/benefit-fe`. Resume from the first step whose gate isn't met.
- Before each step, tell the user which step you're on. Stop at each gate that fails and say what's missing.
- Lane agents: `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane`. Use plan mode in step 2 and review mode in step 5. Run independent lanes in parallel.
- Rule sets and which paths they cover: `project-rules/README.md`.
- Never skip the rules gate (step 5), and confirm with the user before pushing (step 7).
