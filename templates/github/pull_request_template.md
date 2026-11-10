<!--
  PR title: Conventional Commits, e.g. "feat(login): add password reset flow"
  Keep PRs small and focused on one change. Delete sections that don't apply.
-->

## Summary

<!-- What does this PR do and why? 1–3 sentences a reviewer can read in 10 seconds. -->

## Related

<!-- Ticket / issue (use "Closes #123" to auto-close), spec path in ai-immersion-metarepo (specs/NNN-feature/), sibling PRs in other repos. -->

- Ticket:
- Spec:
- Related PRs:

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor (no behaviour change)
- [ ] Docs / config / CI
- [ ] Breaking change (API, schema or contract): describe the impact and migration below

## Changes

<!-- Bullet the notable changes, grouped by area. Call out anything reviewers should look at first. -->

-

## How to test

<!-- Exact commands and steps, plus the results you got. Include test data or env setup if needed. -->

```bash

```

## Screenshots / recordings

<!-- UI changes only: before / after. -->

## Decided automatically - please review

<!-- From specs/NNN-feature/decisions/auto-decisions.json: one line per ADR the decision-maker agent decided.
     Delete this section if there are none. -->

| ADR | Question | Chosen | Architect recommended | Revisit if |
|---|---|---|---|---|
|  |  |  |  |  |

Amendments suggested (not made; need all three team members):

## Deployment notes

<!-- Migrations, new env vars (add to .env.example), feature flags, rollout or rollback steps. Write "None" if not applicable. -->

## Checklist

- [ ] Tests added or updated first (red-green-refactor), and the full suite passes locally
- [ ] Lint and type checks pass
- [ ] No secrets, keys or `.env` files committed; new config is in `.env.example`
- [ ] External input is validated; queries are parameterised; errors don't leak internals
- [ ] Dependency changes scanned (`npm audit` / `pip audit`)
- [ ] Docs / README updated where behaviour changed
- [ ] Self-reviewed the diff

## AI assistance

- [ ] This PR contains AI-generated code (Claude Code / Copilot / Spec Kit), and I have reviewed and understood all of it
- [ ] AI or prompt features checked for prompt injection, PII exposure and bias
