# Security practices
- Treat all external input as untrusted: validate and sanitize at every boundary, and check authorization per-request — never assume an internal call is already trusted.
- Prevent injection: parameterized queries always; sanitize/constrain user input before it's interpolated into any LLM prompt (prompt injection).
- Hash passwords/credentials with a modern algorithm (scrypt/bcrypt/argon2) — never MD5/SHA1.
- No secrets in code or commits: use `.env`/a secrets manager, commit only `.env.example`, and gate `main` behind required PR review plus passing CI (build/test/security-scan).
- Wrap external/network calls with timeouts, TLS verification, and retry/backoff; never fire-and-forget on untrusted calls.
- Don't leak internals in error responses: no stack traces, SQL, or system details in what's returned to the client.
- Scan dependencies for vulnerabilities (`npm audit`, `pip audit`, `dotnet list package --vulnerable`, etc.) in CI, not just manually.
- Before shipping a user-facing AI prompt/feature, check it for bias, PII exposure, and prompt-injection risk — not just task correctness.
