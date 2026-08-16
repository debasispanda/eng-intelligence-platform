# AI Engineering Intelligence Platform

Connected dashboard workspace with a FastAPI/PostgreSQL backend and Next.js
frontend.

## Local verification

Backend:

```bash
cd backend
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run python -m app.seed
uv run fastapi dev app/main.py
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Set `BACKEND_API_BASE_URL` in `frontend/.env.local`. The backend persistence
tests require a PostgreSQL `DATABASE_URL` and a role that can create and drop
temporary schemas.

Validation commands:

```bash
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm run lint && npm run test && npm run build && npm run test:e2e
```

The browser suite starts deterministic local backend stubs and two production
frontend instances to verify live data, profile-menu interaction, and the
explicit backend-error state without external credentials.
