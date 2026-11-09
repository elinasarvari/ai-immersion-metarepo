---
name: create-pr
description: Create a feature branch, commit, push and open a pull request against main for code changes made inside a linked repository under repos/ (git submodule). Use after /speckit-implement or any code change in repos/<name> when the user asks to push, ship, open/create a PR, or raise a pull request.
---

# Create a PR in the linked repository

Code changes live inside the submodule `repos/<name>`; each submodule pushes to its **own** `origin`, so the PR always goes to the right repository. The metarepo is never pushed by this skill.

## Steps

1. **Find the target repo(s).** Run `git -C repos/<name> status --short` for each submodule (list them with `git config -f .gitmodules --get-regexp path`). Only repos with changes or unpushed commits get a PR. If the feature's `specs/<NNN-feature>/plan.md` names target repos, they must match.
2. **Pick the branch name.** Default to the Spec Kit feature name (the `specs/` folder, e.g. `003-user-login`), prefixed by type: `feature/003-user-login` (or `fix/…`). Use the **same branch name in every repo** touched by one feature.
3. **Write the commit message and PR body.**
   - Commit: Conventional Commits, e.g. `feat(login): add password reset flow`.
   - PR body: write to a temporary file (scratchpad / temp dir, not in the repo) with: Summary (from `spec.md`), Changes, How to test (commands you ran and their results), link to the spec path in the metarepo, and links to sibling PRs for multi-repo features.
4. **Confirm with the user** before pushing: show repo, remote URL, branch, files changed, commit message, PR title. Skip only if the user already said to go ahead.
5. **Run, per repo:**

   ```bash
   skills/create-pr/create-pr.sh <repo-name> \
     --branch feature/003-user-login \
     --message "feat(login): add password reset flow" \
     --title "feat(login): add password reset flow" \
     --body-file /path/to/pr-body.md [--draft] [--base main]
   ```

   The script: verifies `repos/<name>` is a registered submodule → fetches `origin/main` → creates/switches to the branch (carrying the uncommitted changes) → commits → pushes with upstream → runs `gh pr create --base main`. Re-running on the same branch adds a new commit and updates the existing PR.
6. **Multi-repo features:** after all PRs exist, edit each PR body to link its siblings (`gh pr edit <url> --body-file …`).
7. **Report** the PR URL(s).

## Rules

- Never commit or push to `main`; never force-push; never use `--no-verify`.
- Run the project's build/tests (from its own README / `project-rules/`) before pushing; report failures instead of pushing broken code unless the user says to open a draft PR (`--draft`).
- Don't push secrets: check the diff for `.env`, keys and tokens before committing.
- Requires `gh auth login`. If `gh` is unauthenticated or the repo isn't on GitHub, use `--no-pr` and give the user the branch name to open the PR manually.
- Do **not** bump the submodule pointer in the metarepo to an unmerged feature branch. After the PR merges, update it with `git submodule update --remote repos/<name>` and commit that in the metarepo (along with the `specs/` folder).
