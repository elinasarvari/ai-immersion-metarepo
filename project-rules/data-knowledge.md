# Knowledge and data lane (`KD-*`)

Applies to `benefit-be/packages/rag/`, `packages/rules/`, `db/`, `analytics/`, `data/policy/` and the retrieval part of `evals/`. Owner: Knowledge & data. SQL rules in [database.md](database.md) also apply.

## Rules engine (`packages/rules/`)
- **KD-1** Pure Python: no I/O, no framework imports, no clock. The entry point is `evaluate(case, as_of_date)`, and the date is always passed in.
- **KD-2** The rules engine is the only thing that decides eligibility (`PR-1`). Every determination lists the rules that fired.
- **KD-3** Every rule has `hypothesis` property tests plus example tests for its edge cases (boundaries, missing data, dates).

## Retrieval (`packages/rag/`)
- **KD-4** Embeddings: Qwen3-Embedding-0.6B, 1024 dimensions, on Mac MPS. Queries get the instruction prefix; documents don't.
- **KD-5** Hybrid search: pgvector HNSW plus Postgres full-text search. Retrieve the top 40, rerank with `bge-reranker-v2-m3`, return the top 5.
- **KD-6** Every chunk has a stable ID and source metadata (document, section, version), which agents cite (`PR-2`).
- **KD-7** Embedding and reranker models are loaded once per process.
- **KD-8** A change to chunking, embeddings, search or reranking runs the retrieval evals. The PR reports the change and must stay above the thresholds.

## Data stores
- **KD-9** Postgres holds cases, rules, determinations, review tasks, the audit log and policy chunks. MongoDB holds documents, extractions, agent traces and notices. Don't mix them.
- **KD-10** Postgres access uses SQLAlchemy 2 async with `asyncpg`. MongoDB access uses PyMongo async.
- **KD-11** Postgres schema changes go only through Alembic migrations in `db/migrations/`. Never edit an applied migration. Each migration has a working downgrade.
- **KD-12** The audit log is append-only.
- **KD-13** Seeds in `db/seeds/` contain synthetic data only (`PR-3`).
- **KD-14** Files go through the `BlobStore` interface, never direct paths.

## Analytics (`analytics/`)
- **KD-15** dbt layers: staging, then marts, then metrics. DuckDB reads Postgres directly; there's no copy step.
- **KD-16** Every metric has a dbt test and a known-answer test. The metrics are time to decision, deadline compliance, automatic renewal rate, procedural denial rate, AI override rate and open-review age.
- **KD-17** The warehouse is refreshed by a Temporal Schedule running `dbt build`, not a cron job.
