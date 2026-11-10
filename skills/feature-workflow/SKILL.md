---
name: feature-workflow
description: Build an existing Benefits Case spec end to end with the Spec Kit workflow engine, each AI step a separate agent - architect plan, decision-maker for open ADRs, tasks and QA tasks, contracts, lanes in parallel, QA tests, verify loop (fix, then parallel tests, builds and script checks, then parallel code and compliance reviews), draft PRs and GitHub Actions - asking a person only when automation can't decide. Use when the user asks to build, implement, deliver or ship a spec or feature, or to start, resume or check a feature run.
---

# Feature workflow

Runs [workflows/benefit-feature/workflow.yml](../../workflows/benefit-feature/workflow.yml); lanes run in parallel inside it. Checks live in `workflows/benefit-feature/scripts/wf.py`, with tests in `workflows/benefit-feature/tests/`.

## Start

The spec must already exist (write it with `/speckit-specify` first). Ask which `pr_mode` the user wants unless they said; starting with `pr_mode=draft` is their approval to push draft PRs.

```bash
specify workflow run workflows/benefit-feature/workflow.yml -i feature=<NNN> [-i pr_mode=draft|ask|none] [-i trace_mode=strict|warn] [-i decision_mode=auto|ask] --json < /dev/null
```

Note the `run_id`. Never pass a `*_verdict` input when starting. `decision_mode=auto` (the default) lets the decision-maker agent settle open ADRs; tell the user the draft PRs list each one for review. Use `ask` only if they want to decide themselves.

## Pauses (only when a person is needed)

| Gate | When | Show | Resume with |
|---|---|---|---|
| `approve_spec` | spec has `[NEEDS CLARIFICATION]` | `spec.md` | `spec_verdict` |
| `approve_decisions` | only with `decision_mode=ask`: an ADR is `Needs decision` or needs an amendment | `decisions/README.md` | `decision_verdict` |
| `approve_pr` | `pr_mode=ask` | `review/verify.md`, `review/trace.md`, the diff | `pr_verdict` |

Help the user answer (edit `spec.md`, or record the ADR answer per `architecture-decision` step 9). Only after their explicit answer: `specify workflow resume <run_id> -i <input>=approve|reject --json < /dev/null`. Never answer for them, and never use one gate's input for another.

## Failures

`specify workflow status <run_id>` names the failed step; its JSON output lists `problems`. Fix, then `specify workflow resume <run_id> --json < /dev/null`.

| Step | Usually means |
|---|---|
| `sync`, `branches` | a repo isn't cloned, isn't clean, or isn't on `main` |
| `feature`, `plan_gate`, `plan_recheck`, `tasks_gate` | a bad input, or the previous AI step's output is incomplete; fix the file it names |
| `decisions_gate` | the decision-maker found no compliant option for an ADR (see `decisions/README.md`), or didn't record a decision fully. Help the user decide it (`architecture-decision` step 9), then resume |
| `final_gate` | still blocking after 3 rounds (a failing job, an open task, a missing or skipped planned test, a file outside its lane, or a review finding); see `review/verify.md` |
| `ci` | GitHub Actions failed on a PR |

AI steps run as `claude -p`, up to four at once, using the user's permission settings. If one fails on a permission, say which; don't change settings yourself.
