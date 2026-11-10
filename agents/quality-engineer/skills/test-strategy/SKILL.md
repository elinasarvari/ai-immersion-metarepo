---
name: test-strategy
description: As the quality engineer, write a feature's test plan (every requirement and acceptance scenario mapped to named test cases at the right level - unit, integration, workflow, contract, end-to-end, eval - with synthetic data and quality gates) and add the test-first and cross-lane [qa] tasks to tasks.md. Use right after tasks are generated, or when the user asks for a test plan, QA tasks or test coverage of a spec.
---

# Test strategy

You are the **quality-engineer agent**. Read `agents/quality-engineer/quality-engineer.agent.md` and `agents/README.md` first. Paths are from the metarepo root.

## 1. Inputs (read once)
- `specs/<NNN-feature>/spec.md`, `plan.md`, `data-model.md`, `contracts/`, `tasks.md`
- `project-rules/testing.md`, and the test rules of the lanes in `scope.json` (`TW-13`–`16`, `AG-16`–`18`, `KD-3`, `KD-8`, `KD-16`, `PL-7`, `FE-12`)
- Existing tests in the target repos: `git -C repos/<repo> ls-files tests '*.test.ts*'`

## 2. Write `specs/<NNN-feature>/test-plan.md`
```markdown
# Test plan: <NNN-feature>

## Cases
| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-010-01, US1-AS1 | unit | data-lane / benefit-be | test_FR_010_01_extension_adds_ten_days | seed: household H3 |

## Quality gates
- Coverage: every FR has ≥1 case (`wf.py tasks-gate`), and every case has a test defined with its exact name and not skipped (`wf.py job <feature_dir> trace:strict`)
- Evals: <metric> ≥ <threshold> (AI features only)
- Not tested, and why: <FR and reason> (should be empty)
```
- **Levels:** `unit`, `integration`, `workflow`, `contract`, `e2e`, `eval`.
- **Lane / repo:** the lane that owns the code under test, or `qa` for cases that span lanes or repos, then the repo (`data-lane / benefit-be`). The trace looks for the test only in that repo.
- **Test name:** exact and unique. Python: the function name, `test_FR_<NNN>_<nn>_…`. TypeScript: the start of the `test('FR-<NNN>-<nn>: …')` title. Eval: the eval case id.

## 3. Add tasks to `specs/<NNN-feature>/tasks.md`
- **Lane tasks:** for each implementation task, make sure its test-first task exists, tagged the same `[lane][repo]`, and names its `TC-` IDs. Add the task where it's missing.
- **`[qa]` tasks:** contract, cross-lane integration, end-to-end journey and eval tasks, tagged `[qa][benefit-be]` or `[qa][benefit-fe]`. They run after all lanes finish.
- Use the next free task numbers. Don't reorder or rewrite existing tasks.

## 4. Self-check, then report
```bash
python3 workflows/benefit-feature/scripts/wf.py tasks-gate <feature_dir>   # task lane tags + test-plan coverage and names
```
Fix what it reports, then reply in ≤10 lines (agent file, section 6).
