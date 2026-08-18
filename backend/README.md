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
uv run python -m app.sync_github
uv run python -m app.sync_jira
uv run python -m app.enqueue_sync github
uv run python -m app.worker
uv run python -m app.scheduler
```

`uv run python -m app.seed` creates the idempotent
`Engineering Intelligence Demo` dataset after migrations have run. It does
not call external services.

`GET /dashboard/overview` serves the organization named by
`DEFAULT_ORGANIZATION_NAME`, which defaults to that demo organization.

`uv run python -m app.sync_github` performs a read-only GitHub synchronization
for repositories, pull requests, and Actions workflow runs. It requires
`GITHUB_TOKEN`, a migrated database, and an existing default organization.

## GitHub token setup

For local development, create a GitHub **fine-grained personal access token**
from GitHub **Settings → Developer settings → Personal access tokens**. Use a
short expiration, select only the required repositories, and grant:

- **Metadata: Read-only**
- **Pull requests: Read-only**
- **Actions: Read-only**

For organization-owned repositories, the token resource owner must be the
organization and the organization may require administrator approval. Store the
token only in the untracked `backend/.env` file or another secret manager:

```env
GITHUB_TOKEN=github_pat_...
```

The current development client calls `/user/repos`, so it synchronizes
repositories visible to the authenticated user. It is not yet a
multi-organization production integration. The production path should use a
GitHub App with organization installation selection, least-privilege
permissions, encrypted credentials, and webhook-based synchronization.

## Jira synchronization

Configure `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, and the
comma-separated `JIRA_PROJECT_KEYS` allowlist in `.env`, then run:

```bash
uv run python -m app.sync_jira
```

The read-only synchronization imports issues, epics, and unreleased/released
versions. Jira labels `risk-high`, `risk-medium`, and `delay-days:N` map to
normalized epic risk and schedule delay. Releases use version dates and
report `0%` until released or `100%` when released because Jira versions do
not provide a normalized completion percentage. Sprint/board ingestion is
deferred until a normalized sprint model is introduced.

## Platform-managed dependencies and workers

PostgreSQL and Redis are managed by the separate `platform` repository. Start
those services there, then configure this backend with the platform-provided
`DATABASE_URL` and `REDIS_URL`.

```bash
# Run from the platform repository
docker compose up -d postgres redis
```

The app-specific Compose file in the repository root builds and runs the local
API, worker, and scheduler image on the platform Compose network. Use the
root `.env` for container hostnames:

```bash
cp .env.example .env
docker compose up --build -d
```

The root environment uses `postgres` and `redis` hostnames. Keep using
`backend/.env` when running commands directly on the host, where those
services are reached through `localhost`.

Jobs can be enqueued with `enqueue_sync("github")` or `enqueue_sync("jira")`
from `app.queue`, or through the CLI:

```bash
uv run python -m app.enqueue_sync github
uv run python -m app.enqueue_sync jira
```

The worker invokes the same synchronization entrypoints used by the CLI.
`GET /health/redis` is available for platform readiness checks.
The scheduler enqueues configured provider jobs at the
`INGESTION_SCHEDULE_SECONDS` interval. It skips providers whose credentials or
project scope are not configured.

Set `LLM_GATEWAY_URL` and optional `LLM_API_KEY` to enable
`GET /dashboard/summary`. The gateway must expose an OpenAI-compatible
`/chat/completions` endpoint. Without it, the endpoint returns `503`.