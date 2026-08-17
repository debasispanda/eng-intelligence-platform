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
uv run python -m app.seed
uv run python -m app.sync_github
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
- Route tests use `httpx.AsyncClient` with `ASGITransport`; do not add the
  deprecated Starlette `TestClient`.
- The seed command creates one idempotent demo organization after migrations;
  it is development-only and must not be used as an integration substitute.
- The unauthenticated overview route scopes data to
  `DEFAULT_ORGANIZATION_NAME`; authentication replaces this development-only
  selection in a later phase.
- GitHub synchronization is currently a bounded, read-only command. Keep
  provider payloads inside `app/integrations/` and map them to normalized
  models before persistence.
- Add a focused test with every route, schema, or configuration change.
