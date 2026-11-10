# Knowledge and data lane (`KD-*`)

Applies to `benefit-be/packages/rag/`, `packages/rules/`, `db/`, `analytics/`, `data/policy/` and the retrieval part of `evals/`. Owner: Knowledge & data. MongoDB rules in [database.md](database.md) also apply.

## Rules engine (`packages/rules/`)
- **KD-1** Pure Python: no I/O, no framework imports, no clock. The entry point is `evaluate(household, as_of_date)`, where `household` is the case's household snapshot (FR-003-19), and the date is always passed in.
- **KD-2** The rules engine is the only thing that decides eligibility (`PR-1`). Every determination lists the rules that fired.
- **KD-3** Every rule has `hypothesis` property tests plus example tests for its edge cases (boundaries, missing data, dates).

## Retrieval (`packages/rag/`)
- **KD-4** Embeddings: Qwen3-Embedding-0.6B, 1024 dimensions, on Mac MPS. Queries get the instruction prefix; documents don't.
- **KD-5** Hybrid search, in the application: cosine similarity over the stored chunk embeddings (numpy, with the passages cached in memory once per process) plus keyword scoring (BM25), fused by reciprocal rank. Retrieve the top 40, rerank with `bge-reranker-v2-m3`, return the top 5. The policy manual is small (25–40 sections), so no vector index or search service is used.
- **KD-6** Every chunk has a stable ID and source metadata (document, section, version), which agents cite (`PR-2`).
- **KD-7** Embedding and reranker models are loaded once per process.
- **KD-8** A change to chunking, embeddings, search or reranking runs the retrieval evals. The PR reports the change and must stay above the thresholds.

## Data stores
- **KD-9** MongoDB is the only operational database. The database `benefit` holds every collection listed in `specs/README.md` except `audit_log`, which lives alone in `benefit_audit` so the runtime user can be limited to insert and find. Household-scoped collections always carry `household_id` (and `case_id` where the record belongs to a case), and every repository query on them includes the household filter.
- **KD-10** MongoDB access uses PyMongo async only, through repository modules. Services and activities never build queries. Multi-document writes (for example a case change plus its audit entry, or an outbox record) use a transaction.
- **KD-11** Collection, validator and index changes go only through versioned migration scripts in `db/migrations/`, applied by the runner, which records them in `_migrations`. Never edit an applied migration. Each migration has a working downgrade.
- **KD-12** The audit log is append-only: the application role may only insert into and read `audit_log` (a restricted MongoDB role), and its validator rejects fields other than the agreed ones.
- **KD-13** Seeds in `db/seeds/` contain synthetic data only (`PR-3`).
- **KD-14** Files go through the `BlobStore` interface, never direct paths.

## Analytics (`analytics/`)
- **KD-15** dbt layers: staging, then marts, then metrics. An export step (`analytics/export_mongo.py`) copies pseudonymised collections from MongoDB into DuckDB staging tables, then dbt builds from them. No personal data is exported.
- **KD-16** Every metric has a dbt test and a known-answer test. The metrics are time to decision, deadline compliance, automatic renewal rate, procedural denial rate, AI override rate and open-review age.
- **KD-17** The warehouse is refreshed by a Temporal Schedule running the MongoDB export and then `dbt build`, not a cron job.
