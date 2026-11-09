---
name: sync-repos
description: Check that the plain git clones under repos/ are healthy, and fast-forward them to the latest default branch (for example after a PR is merged). Use when the user asks to sync, update, refresh or pull the latest of the linked repos, before starting a feature, or when a clone looks broken or out of date.
---

# Sync linked repos

Run from the metarepo root:

```bash
skills/sync-repos/sync-repos.sh --check            # report only, change nothing (exit 1 if broken or behind)
skills/sync-repos/sync-repos.sh                    # fast-forward what's safe to fast-forward
skills/sync-repos/sync-repos.sh benefit-be         # limit to specific repos
```

`repos/` holds plain, git-ignored clones (see `clone-repo` skill) — there is no `.gitmodules` and nothing here is ever recorded in the metarepo's git history.

## What it does

1. **Validates `repos/`:** every entry (other than `.gitkeep`) must be a real git repo. Anything else is flagged as broken.
2. **Fetches** `origin` for each clone.
3. **Fast-forwards** each clone to `origin/<default branch>`, but only when it is clean and on that branch (or detached at a commit already in it).
4. **Leaves alone**, and reports, any clone with a feature branch checked out, uncommitted changes or unpushed commits. It never resets, stashes or forces.

## When to run it

- Before starting work in a cloned repo, with no flags, so it starts from the latest default branch.
- Whenever the user asks if the repos are up to date: `--check`.

## Rules

- Report what was updated, what was left alone and why. For anything left alone, tell the user what to do (for example, finish or merge the feature branch, or commit or stash their changes). Don't do it for them.
- Never commits or stages anything in the metarepo — there's no pointer to record for a plain clone.
