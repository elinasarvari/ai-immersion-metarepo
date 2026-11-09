---
name: review-changes
description: Run the backend and frontend code reviewer agents (plus the lane rule checks) on the current changes in repos/benefit-be and repos/benefit-fe, and combine their findings. Use when the user asks for a code review, asks to review the changes or a branch, or before opening a PR.
---

# Review changes

## 1. Find what changed

For each of `repos/benefit-be` and `repos/benefit-fe`:

```bash
skills/review-changes/branch-status.sh <repo>     # fetches; compares the branch with origin/main
git -C repos/<repo> diff --stat <DIFF>            # DIFF as printed by the script, normally origin/main...HEAD
```

The script compares the current branch with the repo's default branch on GitHub (`main`). It reports how far ahead and behind the branch is, uncommitted files, and whether it would merge cleanly (exit 1 means it would conflict). It changes nothing.

Skip a repo with `AHEAD=0` and `UNCOMMITTED=0`. If the user named a repo, branch or PR, review only that.

## 2. Run the reviewers (in parallel)

| Changed repo | Code reviewer | Rule checks (review mode) |
|---|---|---|
| `benefit-be` | `backend-reviewer` | the lane agents whose paths changed: `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane` (see `project-rules/README.md`) |
| `benefit-fe` | `frontend-reviewer` | `platform-ui-lane` |

Tell each one the repo, the branch and the feature's `specs/<NNN-feature>/` folder. If the user asked for "code review only", skip the lane agents.

If the change alters the API contract (OpenAPI spec, or `packages/domain` models the API returns), have both reviewers look at both repos' sides of it.

## 3. Report

Combine the results into one report:
- **Branch status per repo:** ahead and behind `main`, and merge clean or conflict (from the script).
- **Verdict per repo:** APPROVE only if the code reviewer approves, every lane agent reports PASS, and the branch merges cleanly into `main`.
- **Blocking findings**, most severe first, de-duplicated (if a reviewer and a lane agent report the same thing, keep one entry with both rule IDs).
- **Non-blocking suggestions**, kept short.
- **Spec coverage gaps.**

Don't fix anything unless the user asks. If they do, fix the blocking findings, then ask only the reviewers that raised them to review again.
