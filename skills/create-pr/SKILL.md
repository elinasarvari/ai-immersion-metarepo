---
name: create-pr
description: Create a feature branch, commit, push and open a pull request against main for code changes made inside a cloned repository under repos/. Use after /speckit-implement or any code change in repos/<name> when the user asks to push, ship, open/create a PR, or raise a pull request.
---

# Create a PR in a cloned repository

`repos/<name>` is a plain git clone (made by the **clone-repo** skill and git-ignored by the metarepo, so there are no submodules). Each clone pushes to its **own** `origin`, so the PR always goes to the right repository. This skill never pushes the metarepo.

## Steps

1. **Find the target repo(s).** List the clones with `ls repos/`, then run `git -C repos/<name> status --short` and `git -C repos/<name> log --oneline origin/main..HEAD` for each. Only repos with changes or unpushed commits get a PR. If the feature's `specs/<NNN-feature>/plan.md` names target repos, they must match.
2. **Pick the branch name.** Default to the Spec Kit feature name (the `specs/` folder, e.g. `003-user-login`), prefixed by type: `feature/003-user-login` (or `fix/…`). Use the **same branch name in every repo** touched by one feature.
3. **Check `gh`.** Run `gh auth status`. If it isn't logged in, ask the user to run `gh auth login` (it is interactive, so you can't do it for them), or use `--no-pr`: the script then pushes and prints the GitHub compare link for opening the PR in the browser.
4. **Write the commit message and PR body.**
   - Commit: Conventional Commits, e.g. `feat(login): add password reset flow`.
   - PR body: use the target repo's `.github/pull_request_template.md` if it has one, otherwise `templates/github/pull_request_template.md` from the metarepo. Fill every section (Summary from `spec.md`, the spec path, How to test with the commands you ran and their results, sibling PRs for multi-repo features), tick only the checklist items that are actually true, delete sections that don't apply, and remove the `<!-- -->` hints. Write it to a temporary file (scratchpad or temp dir, not in the repo).
5. **Confirm with the user** before pushing: show repo, remote URL, branch, files changed, commit message, PR title. Skip only if the user already said to go ahead.
6. **Run, per repo,** from anywhere in the metarepo (not from inside `repos/<name>`, which is a separate git repo):

   ```bash
   git create-pr <repo-name> \
     --branch feature/003-user-login \
     --message "feat(login): add password reset flow" \
     --title "feat(login): add password reset flow" \
     --body-file /path/to/pr-body.md [--draft] [--base main] [--no-pr]
   ```

   `git create-pr` is a git alias for `skills/create-pr/create-pr.sh`, defined in the metarepo's committed `.gitconfig`. If git says it isn't a git command, enable it once per clone with `git config --local include.path ../.gitconfig`, or call the script directly with the same arguments.

   The script:
   1. Checks that `repos/<name>` is a git clone with an `origin`.
   2. Checks that `gh` is installed and logged in, unless `--no-pr`. It stops before pushing anything if not.
   3. Fetches `origin/main`, then creates or switches to the branch, carrying any uncommitted changes.
   4. Commits the changes. It refuses to commit `.env`, keyfiles, `.pem` or `id_rsa` files, and runs `gitleaks protect --staged` when gitleaks is installed.
   5. Pushes with upstream, then runs `gh pr create --base main`. With `--no-pr` it prints the compare link instead.

   Re-running on the same branch adds a new commit and updates the open PR.
7. **Multi-repo features:** after all PRs exist, edit each PR body to link its siblings (`gh pr edit <url> --body-file …`).
8. **Report** the PR URL(s), or the compare links when `--no-pr` was used.

## Rules

- Never commit or push to `main`; never force-push; never use `--no-verify`.
- Run the project's build and tests (from its own README and `project-rules/`) before pushing (`make verify` in `benefit-be` runs both repos). Report failures instead of pushing broken code, unless the user asks for a draft PR (`--draft`).
- Don't push secrets: the script blocks the common cases, but still read the diff before committing.
- The metarepo never records the clones. After the PRs merge, fast-forward the clones with the **sync-repos** skill, and commit only the metarepo's own files (such as `specs/`) in the metarepo.
