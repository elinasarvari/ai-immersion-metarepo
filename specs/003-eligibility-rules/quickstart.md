# Quickstart: validate 003

Prerequisites: both clones on `feature/003-eligibility-rules`, merged with `origin/main` (ADR-003-04); `make setup` done in `repos/benefit-be`.

| # | Check | Command (in `repos/benefit-be` unless noted) | Expected |
|---|---|---|---|
| 1 | Engine and known answers (US1–US3, SC-003-01) | `uv run pytest tests/packages/rules -q` | all pass, twice in a row |
| 2 | Purity (FR-003-08) | `uv run pytest tests/contract/test_rules_purity.py` | pass |
| 3 | Seed reproducible (US4, SC-003-03) | `make seed-reset` twice; compare `db/seeds/generated/manifest.json` | identical hashes |
| 4 | Data set shape (FR-003-10–13) | `uv run pytest tests/db/seeds tests/integration/test_seeded_dataset.py` | pass, no xfail |
| 5 | Migration up/down | `uv run pytest tests/db/test_migrations.py` | 0001…0005 up and down |
| 6 | Worker path (ADR-003-02/03) | `uv run pytest tests/integration -k determination` | A eligible, B ineligible (income), C cannot determine |
| 7 | API (ADR-003-05) | `uv run pytest tests/apps/api -k determinations` | 200 caseworker, 403 applicant |
| 8 | Case page (US5) | in `repos/benefit-fe`: `pnpm test` then `pnpm e2e` after `make dev` + `make seed-reset` | section shows result, reason, as-of date, rule set version, six rules; missing items for C |
| 9 | Everything | `make check` (both repos) | green |

Contracts: [rules-interface.md](contracts/rules-interface.md), [rest-api.openapi.yaml](contracts/rest-api.openapi.yaml). Models: [data-model.md](data-model.md).
