# Backend rules (Python + FastAPI)
- Python 3.11+, type hints everywhere, `ruff` for lint/format, `pytest` for tests.
- Layers: `routers/` → `services/` → `repositories/`; no business logic in routers.
- Pydantic models for all request/response bodies.
- Every endpoint ships with a test in `tests/`.
- Folder layout, runtime processes and import boundaries: see [backend-architecture.md](backend-architecture.md). It takes precedence where the two differ.
