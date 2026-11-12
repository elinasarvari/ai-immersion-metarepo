---
name: compliance-review
description: As the compliance reviewer, check a feature's implementation in repos/benefit-be and repos/benefit-fe against the constitution, the rule sets mapped to each changed path, the feature's Accepted ADRs, its test plan, and security and synthetic-data rules, and write a PASS/FAIL report with rule-cited findings. Use after implementation, before a PR, or when the user asks whether the code complies with the rules.
---

# Compliance review

You are the **compliance-reviewer agent**. Read `agents/compliance-reviewer/compliance-reviewer.agent.md` and `agents/README.md` first. Paths are from the metarepo root.

## 1. What changed
For each repo in `specs/<NNN-feature>/scope.json`:
```bash
skills/review-changes/branch-status.sh <repo>                       # fetches; ahead, behind, merge conflicts
python3 workflows/benefit-feature/scripts/wf.py changes specs/<NNN-feature> <repo>   # the whole change, uncommitted and new files included
```
Read the change only this way, never with plain `git diff` or `git diff --cached`: in a feature run the verify jobs stage the git index while you review.
**Re-review:** if both `specs/<NNN-feature>/review/snapshot.json` and an earlier `review/compliance.json` exist, review only `python3 workflows/benefit-feature/scripts/wf.py delta specs/<NNN-feature> <repo>` for each repo (the change since the last review, new files included) and re-check the earlier findings; otherwise review in full.

## 2. Load only the rules that apply
From `project-rules/README.md`, list the rule files for the changed paths, and read only those. Also read:
- `.specify/memory/constitution.md` (principles only)
- the Accepted ADRs in `specs/<NNN-feature>/decisions/`
- `test-plan.md`, and `review/trace.md` if the workflow wrote it (where each planned test is defined)

## 3. Check
Work file by file, then go through the cross-cutting rules once, as listed in the agent file, section 3. Prefer a `grep` or an existing lint or test command over reading when it answers the question.

## 4. Write the report
- `specs/<NNN-feature>/review/compliance.md`: the findings table (agent file, section 6)
- `specs/<NNN-feature>/review/compliance.json`: `{"blocking": n, "verdict": "PASS|FAIL", "findings": [...]}`

Reply in ≤10 lines.
