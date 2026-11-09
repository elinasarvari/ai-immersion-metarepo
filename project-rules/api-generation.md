# API generation from OpenAPI specs
- Validate the OpenAPI spec (3.0+) for completeness before generating any code; flag ambiguous schemas, auth methods, or missing requirements instead of guessing.
- Scaffold with clear separation of concerns: controllers/handlers → services (business logic) → repositories/data access → models/DTOs.
- Implement auth from the spec's declared security schemes; don't hardcode a method the OpenAPI doc doesn't specify.
- Every generated endpoint ships with unit tests plus a README covering setup, env vars, and how to run it.
- Include input validation, structured error handling, and logging in every generated layer, not just the happy path.
- Add a committed `.env.example` and gitignore the real `.env`; never put secrets in generated config.
