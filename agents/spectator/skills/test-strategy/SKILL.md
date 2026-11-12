---
name: test-strategy
description: As the spectator, write a feature's test plan (every requirement and acceptance scenario mapped to named test cases at the right level - unit, integration, workflow, contract, end-to-end, eval - each with its lane and repo, synthetic data and quality gates) after the plan and its decisions are settled and before any task exists, so the tasks step writes the test-first and [qa] tasks in its one pass. Use right after planning, or when the user asks for a test plan or test coverage of a spec.
---

# Test strategy

You are the **spectator agent**. Read `agents/spectator/spectator.agent.md` and `agents/README.md` first. Paths are from the metarepo root.

## 1. Inputs (read once)
- `specs/<NNN-feature>/brief.md` first (the architect's summary: FRs, rule IDs, modules, existing tests), then `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `quickstart.md` and the ADRs as decided (`decisions/`). No `tasks.md` exists yet.
- `project-rules/testing.md`, and the test rules of the lanes in `scope.json` (`TW-13`–`16`, `AG-16`–`18`, `KD-3`, `KD-8`, `KD-16`, `PL-7`, `FE-12`)
- Existing tests in the target repos, where the brief doesn't list them: `git -C repos/<repo> ls-files tests '*.test.ts*'`

## 2. Write `specs/<NNN-feature>/test-plan.md`
```markdown
# Test plan: <NNN-feature>

## Cases
| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-010-01, US1-AS1 | unit | data-lane / benefit-be | test_FR_010_01_extension_adds_ten_days | seed: household H3 |

## Quality gates
- Coverage: every FR has ≥1 case (`wf.py test-gate`), and every case has a test defined with its exact name and not skipped (`wf.py job <feature_dir> trace:strict`)
- Evals: <metric> ≥ <threshold> (AI features only)
- Not tested, and why: <FR and reason> (should be empty)
```
- **Levels:** `unit`, `integration`, `workflow`, `contract`, `e2e`, `eval`.
- **Failure paths, not just the happy path.** Plan a case for each of these the plan creates; reviewers block on them when they are missing:
  - every Temporal activity whose retries run out: what the workflow does, and that the case isn't left open or locked (TW-10);
  - every API error response in `contracts/` (each 4xx and 5xx, including races and another household's data), asserting the documented error body;
  - every Accepted ADR's "How we verify it";
  - every refusal or rejection the spec or an ADR requires to be recorded (audit, constitution IV).
- **Each case must prove what it says.** Its data must put the system in the state the case names (for example a *decided* case for "action on a decided case"); say that state in the Data column.
- **Lane / repo:** the lane that owns the code under test, or `qa` for cases that span lanes or repos, then the repo (`data-lane / benefit-be`). The trace looks for the test only in that repo.
- **Test name:** exact and unique. Python: the function name, `test_FR_<NNN>_<nn>_…`. TypeScript: the start of the `test('FR-<NNN>-<nn>: …')` title. Eval: the eval case id.
- **Quickstart:** each step a person would check in the browser becomes an `e2e` case (the verify loop's e2e job runs it), not a task.
- **Every case becomes a task.** The tasks step writes a test-first task in the case's lane for each lane case, and a `[qa]` task for each `qa` case, naming its `TC-` ID; `wf.py tasks-gate` fails if a case has no task. So the Lane / repo column must be exact.
- **Update mode** (an earlier run left `test-plan.md`): extend it. Keep every existing case, its ID and its test name, correct a case only where the spec changed it, and add cases with the next free TC numbers for new or changed requirements.

## 3. Self-check, then report
```bash
python3 workflows/benefit-feature/scripts/wf.py test-gate <feature_dir>   # levels, repos, names, every FR covered
```
Fix what it reports, then reply in ≤10 lines (agent file, section 6).
