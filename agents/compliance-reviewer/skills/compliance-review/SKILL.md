---
name: compliance-review
description: As the compliance reviewer, check a feature's implementation in repos/benefit-be and repos/benefit-fe against the constitution, the rule sets mapped to each changed path, the feature's Accepted ADRs, its test plan, and security and synthetic-data rules, and write a PASS/FAIL report with rule-cited findings. Use after implementation, before a PR, or when the user asks whether the code complies with the rules.
---

# Compliance review

You take on the **compliance reviewer role**. Read `agents/compliance-reviewer/rules/behavior.md` and `agents/README.md` first. Paths are from the metarepo root.

## 1. What changed
For each repo in `specs/<NNN-feature>/scope.json`:
```bash
skills/review-changes/branch-status.sh <repo>                       # fetches; prints DIFF (origin/main...HEAD)
git -C repos/<repo> diff --name-only origin/main...HEAD; git -C repos/<repo> status --short
```
**Re-review:** if `specs/<NNN-feature>/review/snapshot.json` exists, review only `git -C repos/<repo> diff <snapshot[repo]>` and re-check the findings in the earlier `review/compliance.json`.

## 2. Load only the rules that apply
From `project-rules/README.md`, list the rule files for the changed paths, and read only those. Also read:
- `.specify/memory/constitution.md` (principles only)
- the Accepted ADRs in `specs/<NNN-feature>/decisions/`
- `test-plan.md`

## 3. Check
Work file by file, then go through the cross-cutting rules once, as listed in behavior section 3. Prefer a `grep` or an existing lint or test command over reading when it answers the question.

## 4. Write the report
- `specs/<NNN-feature>/review/compliance.md`: the findings table (behavior section 6)
- `specs/<NNN-feature>/review/compliance.json`: `{"blocking": n, "verdict": "PASS|FAIL", "findings": [...]}`

Reply in ≤10 lines.
