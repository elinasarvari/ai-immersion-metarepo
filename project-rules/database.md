# Database conventions: MongoDB

Applies to everything that talks to the database: `db/`, the repository modules in `apps/api/`, `apps/worker/` and `packages/mcp_servers/`, and `analytics/`. MongoDB is the only operational database (see [data-knowledge.md](data-knowledge.md), KD-9 to KD-12).

- Never build a query from user input by string or by merging raw request data into a filter. Build filters from typed values (Pydantic models, `UUID`, enums), so an input like `{"$ne": null}` can't become an operator (NoSQL injection). Never use `$where`, `$function` or `$accumulator`.
- Every household-scoped collection carries `household_id`, and `case_id` when the record belongs to a case. Every repository query on it includes the household filter built from the caller's `Principal` or the system credential. A repository call with no principal raises instead of returning data.
- Index the fields that queries filter or sort on, and no others. Compound indexes follow equality, sort, range order. Check new or changed queries on large collections with `explain("executionStats")` before merging.
- Always send a projection: return only the fields the caller needs. No unbounded `find`: paginate with a range on an indexed field (for example `_id` or `occurred_at`) and a `limit`.
- Enforce integrity in the database, not only in code: a `$jsonSchema` validator on every collection (required fields, types, enums, `additionalProperties: false`, patterns), unique indexes for natural keys, and a collation (strength 2) for case-insensitive keys such as `username`.
- Store timestamps as BSON dates in UTC and compute dates and day counts in America/Chicago in code. Store IDs as UUIDs.
- Use one transaction for any write that touches more than one document and must succeed or fail together (a case change and its audit entry, an outbox record). This needs the replica set that `make mongo-up` starts.
- Use two database users: `benefit_owner` (migrations and reset only) and `benefit_app` (runtime, least privilege). The runtime user may only insert into and read `audit_log`.
- Batch bulk writes with `insert_many` or `bulk_write`, not one write per loop turn.
- No real personal data in any collection, fixture or seed (`PR-3`). The `_meta` collection marks the database as synthetic.
