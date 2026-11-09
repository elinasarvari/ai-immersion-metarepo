# Database & SQL conventions
- Always use parameterized queries; never build SQL via string concatenation or f-strings.
- Every new/changed query gets an index on its frequently filtered/joined columns; avoid over-indexing (it slows INSERT/UPDATE).
- No `SELECT *` in production queries; select only the columns needed.
- Prefer JOINs over correlated subqueries; use `EXISTS` instead of `IN` for subqueries where appropriate.
- Run `EXPLAIN ANALYZE` (or the engine equivalent) on new/changed queries touching large tables before merging.
- PostgreSQL specifics: use `TIMESTAMPTZ` over `TIMESTAMP`, `JSONB` with containment operators (`@>`, `?`) over loosely-typed JSON, and enable Row Level Security for multi-tenant tables.
- Enforce data integrity with constraints (foreign keys, `CHECK`, `NOT NULL`) rather than relying solely on application code.
- Batch bulk writes/updates instead of row-by-row loops; paginate large result sets (LIMIT/keyset) instead of returning full tables.
