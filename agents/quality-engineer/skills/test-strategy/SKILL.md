---
name: test-strategy
description: As the quality engineer, write a feature's test plan (every requirement and acceptance scenario mapped to named test cases at the right level - unit, integration, workflow, contract, end-to-end, eval - with synthetic data and quality gates) and add the test-first and cross-lane [qa] tasks to tasks.md. Use right after tasks are generated, or when the user asks for a test plan, QA tasks or test coverage of a spec.
---

# Test strategy

You take on the **quality engineer role**. Read `agents/quality-engineer/rules/behavior.md` and `agents/README.md` first. Paths are from the metarepo root.

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
- Coverage: every FR has ≥1 case (checked by `wf.py test-plan-check` and `wf.py trace`)
- Evals: <metric> ≥ <threshold> (AI features only)
- Not tested, and why: <FR and reason> (should be empty)
```
- **Levels:** `unit`, `integration`, `workflow`, `contract`, `e2e`, `eval`.
- **Lane:** the one that owns the code under test, or `qa` for cases that span lanes or repos.

## 3. Add tasks to `specs/<NNN-feature>/tasks.md`
- **Lane tasks:** for each implementation task, make sure its test-first task exists, tagged the same `[lane][repo]`, and names its `TC-` IDs. Add the task where it's missing.
- **`[qa]` tasks:** contract, cross-lane integration, end-to-end journey and eval tasks, tagged `[qa][benefit-be]` or `[qa][benefit-fe]`. They run after all lanes finish.
- Use the next free task numbers. Don't reorder or rewrite existing tasks.

## 4. Self-check, then report
```bash
python3 workflows/benefit-feature/scripts/wf.py test-plan-check <feature_dir>
python3 workflows/benefit-feature/scripts/wf.py tasks-split <feature_dir>
```
Fix what they report, then reply in ≤10 lines (behavior, section 6).
