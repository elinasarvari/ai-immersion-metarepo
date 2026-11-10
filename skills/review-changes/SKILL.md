---
name: review-changes
description: Review the current changes in repos/benefit-be and repos/benefit-fe outside the workflow - the backend and frontend code reviewers plus the compliance review, in parallel - and combine their findings. Use when the user asks for a code review, a compliance check, or to review the changes or a branch before a PR.
---

# Review changes

1. **What changed:** for each repo, `skills/review-changes/branch-status.sh <repo>` (fetches; reports ahead/behind `origin/main`, uncommitted files and merge conflicts; changes nothing). Skip repos with `AHEAD=0` and `UNCOMMITTED=0`. Find the feature from the branch name `feature/<NNN-feature>`.
2. **Run in parallel:** `backend-reviewer` (if `benefit-be` changed), `frontend-reviewer` (if `benefit-fe` changed), and the `compliance-review` skill. Each writes its `.md` and `.json` to `specs/<NNN-feature>/review/` (`agents/README.md`).
3. **Report** in ≤15 lines: branch status per repo; verdict per repo (APPROVE only if no critical or major finding anywhere and the merge is clean); the blocking findings, most severe first and de-duplicated; and the paths to the full reports.

Don't fix anything unless asked. If asked, first run `python3 workflows/benefit-feature/scripts/wf.py snapshot <feature_dir>`, then fix, then re-run only the reviews that had blocking findings; they'll read just the change since the snapshot.
