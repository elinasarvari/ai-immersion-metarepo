---
name: feature-workflow
description: Build an existing Benefits Case spec end to end with the Spec Kit workflow engine, each AI step a separate agent - spec clarifier for open spec questions, architect plan and brief, decision-maker for open ADRs, the spectator's test plan, tasks written once from both, contracts, lanes and QA tests in parallel, verify loop (fixers per repo, the integrator if main moved, then tests, builds, e2e and script checks in the background while the code and compliance reviews run), draft PRs and GitHub Actions - asking a person only when automation can't decide. Use when the user asks to build, implement, deliver or ship a spec or feature, or to start, resume or check a feature run.
---

# Feature workflow

Runs [workflows/benefit-feature/workflow.yml](../../workflows/benefit-feature/workflow.yml); lanes run in parallel inside it. Checks live in `workflows/benefit-feature/scripts/wf.py`, with tests in `workflows/benefit-feature/tests/`.

## Start

The spec must already exist (write it with `/speckit-specify` first). There are no modes, so don't ask for one: the spec clarifier answers open spec questions, the decision-maker settles open ADRs, the spectator plans the tests, and once everything passes the run pushes the feature branch, opens draft PRs, fixes GitHub Actions failures on the feature branch and marks the PRs ready for review when CI is green. Asking to build or run the feature is the approval to push its feature branch and open PRs; nothing is ever pushed to `main`.

```bash
workflows/benefit-feature/run.sh start <NNN> [-i trace_mode=strict|warn] [-i coding_model=sonnet|opus] [-i judgement_model=opus] [-i test_plan_model=sonnet|opus] < /dev/null
```

Always use `run.sh`, never `specify workflow run` directly: it runs the preflight, creates the feature's own git worktree, and passes `.claude/settings.json` to every agent step with `--settings`, which works even if the folder was never trusted. Without it, agent steps can't write and end with "Prompt exited with code 1". Tell the user they can follow the run live with `workflows/benefit-feature/run.sh watch <NNN>` in a second terminal.

**Worktree.** The run happens in `../ai-immersion-metarepo.worktrees/<NNN-feature>/` (a worktree of the metarepo on `feature/<NNN-feature>`, with `repos/<name>` as worktrees of the main clones on the same branch), so the user's checkout and clones stay free and features can run side by side. Tell the user:
- the plan, ADRs, tasks and reviews are written in the worktree's `specs/<NNN-feature>/`; read and edit them there (gate answers too), and commit them there;
- the run uses the committed agents, rules and workflow. If `start` warns about uncommitted ones, ask whether to commit first or use `run.sh start --in-place <NNN>` (the old way, in the checkout).

`run.sh worktrees` lists them. After the PRs merge, offer `run.sh cleanup <NNN>`. It deletes folders, so ask first, then pass `--yes`. It refuses while anything is uncommitted and keeps the branches.

Note the `run_id`. Never pass `spec_verdict` when starting. Tell the user the draft PRs list each spec answer and ADR decision the agents made, for review there.

## Pauses (only when a person is needed)

| Gate | When | Show | Resume with |
|---|---|---|---|
| `approve_spec` | the spec clarifier left a question only a person can answer (why: `clarifications.json`) | `spec.md` | `spec_verdict` |

Help the user answer in the worktree's `spec.md`. Only after their explicit answer: `workflows/benefit-feature/run.sh resume <run_id> -i spec_verdict=approve|reject < /dev/null`. Never answer for them. The only other stop for a person is `decisions_gate` (below), when the decision-maker finds no compliant option.

## Failures

`python3 workflows/benefit-feature/scripts/watch.py <run_id> --once` shows every stage, the failed step, its last output and the usual cause (`run.sh status <run_id>` gives the engine's own view; always pass the id, since without one it lists every run). Fix it in the worktree, then `workflows/benefit-feature/run.sh resume <run_id> < /dev/null` (`run.sh` finds the run's worktree by its id, or by the feature number).

| Step | Usually means |
|---|---|
| `sync`, `branches` | a repo isn't cloned, or a clone worktree isn't clean or isn't on the feature branch |
| `feature`, `plan_gate`, `plan_recheck`, `test_gate`, `tasks_gate` | a bad input, or the previous AI step's output is incomplete (plan or `brief.md`; `test-plan.md`; `tasks.md`, including a test case or ADR no task names); fix the file it names |
| `spec_check` | the spec clarifier left an answer incomplete in `clarifications.json` (no answer, kind or revisit-if) or the spec no longer passes `prepare`'s checks. Fix the record or the spec, then resume |
| `decisions_gate` | the decision-maker found no compliant option for an ADR (see `decisions/README.md`), or didn't record a decision fully. Help the user decide it (`architecture-decision` step 9), then resume |
| `final_gate` | still blocking when the verify loop stopped, after 2 rounds without progress or 6 rounds (a failing job, an open task, a missing or skipped planned test, a file outside its lane, or a review finding); see `review/verify.md` |
| `ci_gate` | GitHub Actions still red after 3 CI fix rounds; see `review/ci.md` |

AI steps run as `claude -p`, up to four at once, with the permissions in `.claude/settings.json` (passed by `run.sh`). If one fails on a permission, say which command was refused and suggest the allow rule; don't change settings yourself.
