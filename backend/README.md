# Engineering Intelligence Backend

FastAPI service for the Engineering Intelligence Platform.

## Setup

```bash
uv sync
cp .env.example .env
```

Set `DATABASE_URL` in `.env` to the platform-provided PostgreSQL instance
with pgvector on port 5432. `DATABASE_SCHEMA` is configurable and currently
defaults to `public` to preserve the existing tables; the planned target schema
is `platform`.

Persistence tests create and remove a uniquely named temporary PostgreSQL
schema. The configured database role therefore needs permission to create and
drop schemas in the development database.

## Commands

```bash
uv run fastapi dev app/main.py
uv run ruff check .
uv run pytest
uv run pytest tests/test_health.py
uv run pytest tests/test_health.py::test_health_check_returns_ok
uv run python -m app.seed
```

`uv run python -m app.seed` creates the idempotent
`Engineering Intelligence Demo` dataset after migrations have run. It does
not call external services.