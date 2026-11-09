---
name: sync-repos
description: Check that .gitmodules and the submodules under repos/ are healthy, and bring them up to the latest main (for example after a PR is merged). Use when the user asks to sync, update, refresh or pull the latest of the linked repos, after PRs merge, before starting a feature, or when a submodule looks broken or out of date.
---

# Sync linked repos

Run from the metarepo root:

```bash
skills/sync-repos/sync-repos.sh --check            # report only, change nothing (exit 1 if broken or behind)
skills/sync-repos/sync-repos.sh                    # fix and fast-forward, don't commit
skills/sync-repos/sync-repos.sh --commit           # same, then commit the merged pointer updates
skills/sync-repos/sync-repos.sh benefit-be         # limit to specific repos
```

## What it does

1. **Validates `.gitmodules`:** every submodule is under `repos/`, has a URL and is recorded in git. Stray folders in `repos/` are flagged. If a local URL has drifted from `.gitmodules`, it re-syncs it.
2. **Initialises** any submodule that hasn't been fetched yet.
3. **Fast-forwards** each submodule to `origin/<default branch>`, but only when it is clean and on that branch (or detached at a commit already in it).
4. **Leaves alone**, and reports, any submodule with a feature branch checked out, uncommitted changes or unpushed commits. It never resets, stashes or forces.
5. **Updates the metarepo pointers** only for commits already merged into `main`. A pointer at an unmerged feature branch is never recorded.

## When to run it

- At the start of `feature-workflow` (step 0), with no flags, so new branches start from the latest `main`.
- After PRs merge (`feature-workflow` step 8), with `--commit`, to record the new pointers.
- Whenever the user asks if the repos are up to date: `--check`.

## Rules

- Report what was updated, what was left alone and why. For anything left alone, tell the user what to do (for example, finish or merge the feature branch, or commit or stash their changes). Don't do it for them.
- `--commit` creates a local commit in the metarepo only. Push it only if the user asks.
