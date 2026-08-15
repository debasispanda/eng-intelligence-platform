# Backend Agent Guide

## Commands

Run commands from `backend/`:

```bash
uv sync
uv run fastapi dev app/main.py
uv run ruff check .
uv run pytest
uv run pytest tests/test_file.py
uv run pytest tests/test_file.py::test_name
```

## Conventions

- Configure the service through `app/core/config.py`; do not read environment
  variables directly in routes or services.
- Keep routes thin. Put response models in `app/schemas/` and domain or
  persistence behavior outside route modules.
- Use `DATABASE_URL` and `DATABASE_SCHEMA` for the platform
  PostgreSQL/pgvector instance. Existing tables remain in `public` until the
  planned schema cutover. Never commit `.env` files or credentials.
- Persistence tests use a generated temporary schema and drop it during
  teardown; run them only with a development database role that can create and
  drop schemas.
- Add a focused test with every route, schema, or configuration change.
