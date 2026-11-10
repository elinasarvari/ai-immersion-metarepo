---
name: review-changes
description: Review the current changes in repos/benefit-be and repos/benefit-fe outside the workflow - the backend-reviewer, frontend-reviewer and compliance-reviewer agents as parallel subagents - and combine their findings. Use when the user asks for a code review, a compliance check, or to review the changes or a branch before a PR.
---

# Review changes

1. **What changed:** for each repo, `skills/review-changes/branch-status.sh <repo>` (fetches; reports ahead/behind `origin/main`, uncommitted files and merge conflicts; changes nothing). Skip repos with `AHEAD=0` and `UNCOMMITTED=0`. Find the feature from the branch name `feature/<NNN-feature>`.
2. **Pick the reviews:** `python3 workflows/benefit-feature/scripts/wf.py review-list specs/<NNN-feature>`. It lists the reviews to run (all three the first time; afterwards only those with no result, still blocking, or whose repo changed), and records the trees they'll see so a re-review reads only `wf.py delta`.
3. **Run them in parallel, as separate subagents:** `backend-reviewer`, `frontend-reviewer` and `compliance-reviewer`, whichever step 2 listed, each in its own context. Each writes its `.md` and `.json` to `specs/<NNN-feature>/review/` (`agents/README.md`).
4. **Report** in ≤15 lines: branch status per repo; verdict per repo (APPROVE only if no critical or major finding anywhere and the merge is clean); the blocking findings, most severe first and de-duplicated; and the paths to the full reports.

Don't fix anything unless asked. After a fix, start again at step 2: it reruns only the reviews that need it, and they read just the change since they last looked. (If `review-list` returns nothing because an old `review/jobs/*.json` from a workflow run is failing, rerun that job with `wf.py job` first.)
