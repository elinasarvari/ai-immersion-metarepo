# ai-immersion-metarepo

Central store for the AI-assisted development assets shared by the Benefit projects:

| Folder | Purpose |
|---|---|
| `workflows/` | Multi-step agent workflows (spec → plan → implement → review gate → PR) |
| `agents/` | Lane agents (Workflows, Agents, Knowledge & data, Platform & UI) that plan and check the rule sets, plus the `backend-reviewer` and `frontend-reviewer` code reviewers |
| `skills/` | Reusable skills / slash commands (one folder per skill, with `SKILL.md`) |
| `specs/` | Functional specs and technical plans per feature |
| `project-rules/` | Rule sets with IDs, mapped to repo paths in `project-rules/README.md` |
| `templates/` | Starter templates for specs, plans and rule files |

## Projects governed by this repo

- [benefit-fe](https://github.com/OWNER/benefit-fe) — React frontend
- [benefit-be](https://github.com/OWNER/benefit-be) — Python backend

Each project's `CLAUDE.md` points back to the rules in `project-rules/`.

## Linked repositories

Project repos are plain git clones under `repos/`, which is git-ignored (no submodules). Ask Claude Code or GitHub Copilot to "add <url>", or run directly:

```bash
skills/clone-repo/clone-repo.sh https://github.com/OWNER/benefit-fe.git
```

After cloning this metarepo, clone each project repo with `skills/clone-repo/clone-repo.sh <url>`, and keep them current with `skills/sync-repos/sync-repos.sh`.

`.claude/skills` and `.github/skills` are symlinks to `skills/`, so both tools discover the same skills.

## Code review agents

Two agents review code before it goes to a PR. They work the same in Claude Code and in Copilot Chat (agent mode).

| Agent | Reviews | Checks |
|---|---|---|
| `backend-reviewer` | `repos/benefit-be` | bugs (including async and transaction mistakes), Temporal determinism, security (role and case-access checks on every route and MCP tool), import boundaries, API contract changes, AI never deciding eligibility and always citing sources, tests |
| `frontend-reviewer` | `repos/benefit-fe` | state and effect bugs, TanStack Query usage, security (XSS, token storage), the generated API client matching the backend, AI content labelled and overridable, accessibility, loading, empty and error states, Vitest and Playwright tests |

Both also check that everything the feature's spec (`specs/<NNN-feature>/`) marks as done is actually built. They read the changed files in full, can run checks such as `make check`, `pytest` or `tsc` to confirm a finding, and **never edit code**.

### How to run a review

Type `/review-changes` in Claude Code or Copilot Chat, or just ask "review my changes". Add a repo name to limit it, for example `/review-changes benefit-fe`.

To run one reviewer on its own, ask for it by name, for example "use the backend-reviewer agent on benefit-be".

### What happens

1. **Branch check.** For each repo, `skills/review-changes/branch-status.sh` fetches from GitHub and compares your branch with `origin/main`. It reports commits ahead and behind, uncommitted files, and whether the branch would merge cleanly. Repos with no changes are skipped.
2. **Review.** The code reviewer for each changed repo runs in parallel with the lane agents for the folders you touched. The lane agents check the rule sets in `project-rules/`, citing rule IDs like `TW-3`:

   | Repo changed | Code reviewer | Lane checks |
   |---|---|---|
   | `benefit-be` | `backend-reviewer` | `workflows-lane`, `agents-lane`, `data-lane`, `platform-ui-lane` (only those whose folders changed) |
   | `benefit-fe` | `frontend-reviewer` | `platform-ui-lane` |

   Ask for "code review only" to skip the lane checks.
3. **Report.** One report per repo:

   ```
   ## Backend review: REQUEST CHANGES
   Branch: feature/003-user-login → origin/main · 4 ahead, 2 behind · Merge: clean · Spec: specs/003-user-login/

   ### Blocking
   | # | Severity | File:line | Problem | Why it matters | Suggested fix | Rule/FR |
   ### Non-blocking
   ### Spec coverage
   ### Checks run
   ```

### Verdicts

- **APPROVE** only when the code reviewer has no critical or major findings, every lane check passes, and the branch merges cleanly into `main`.
- **Severity:** `critical` = security hole, data loss, wrong eligibility decision, data shown to the wrong role. `major` = bug, missing required test, rule violation, accessibility failure. `minor` = worth fixing before merge. Critical and major block the PR.
- **Branch status:** a merge conflict with `main` always blocks. Being behind `main` is only a note, unless the newer `main` commits touch the same files and break your change.

### After the review

Ask "fix the blocking findings" to have them fixed. Only the agents that raised them review again. When every repo is approved, open the PR (below).

## Opening PRs

### Before you start (once)

```bash
gh auth login        # the GitHub CLI opens the PRs
```

### Open the PR: `/create-pr`

Once the review approves, type `/create-pr` or ask "create a PR". The agent:
1. Picks the branch name from the spec folder (`specs/003-user-login/` → `feature/003-user-login`), using the same name in both repos if the feature touches both.
2. Writes the commit message (Conventional Commits) and fills the PR description from [templates/github/pull_request_template.md](templates/github/pull_request_template.md), including the review results and test commands.
3. **Shows you the repo, branch, files and PR title, and waits for your OK.**
4. Runs `skills/create-pr/create-pr.sh` for each repo: branch from `origin/main`, commit, push to that repo's own GitHub remote, open a PR against `main`. Running it again on the same branch adds a commit to the existing PR.

If the API contract changed, the `benefit-be` PR is opened first, then the `benefit-fe` PR that regenerates the client, and the two link to each other. The script never pushes to `main`, force-pushes or skips git hooks.

To run it yourself:

```bash
skills/create-pr/create-pr.sh benefit-fe \
  --branch feature/003-user-login \
  --message "feat(login): add login page" \
  --title "feat(login): add login page" \
  --body-file pr-body.md          # optional; add --draft for a draft PR
```

### After the PR merges: `/sync-repos`

Type `/sync-repos` or ask "sync the repos". It brings each clean clone in `repos/` up to the latest `main`. Clones with a feature branch or uncommitted changes are reported and left alone.

### The whole flow in one command

`/feature-workflow` runs everything from spec to PR ([workflows/feature.md](workflows/feature.md)) and stops at each gate, including the code review above.

## Claude Code and GitHub Copilot

Both tools share `skills/`, `agents/` and `project-rules/`. Copilot's own files (`.github/copilot-instructions.md` and the slash commands in `.github/prompts/`) are generated from `CLAUDE.md` and the skills:

```bash
python3 scripts/sync-copilot.py          # regenerate
python3 scripts/sync-copilot.py --check  # fail if out of date
```
