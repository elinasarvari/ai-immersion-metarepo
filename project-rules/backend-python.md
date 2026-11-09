# Backend rules (Python + FastAPI)
- Python 3.11+, type hints everywhere, `ruff` for lint/format, `pytest` for tests.
- Layers: `routers/` → `services/` → `repositories/`; no business logic in routers.
- Pydantic models for all request/response bodies.
- Every endpoint ships with a test in `tests/`.
