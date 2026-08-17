# Architecture

## Tech Stack

-   Frontend: React + TypeScript
-   Backend: FastAPI (Python)
-   Database: PostgreSQL + pgvector
-   Background Workers: Python
-   Realtime: WebSockets/SSE
-   LLM Gateway: LiteLLM
-   Deployment: Docker (Kubernetes later)

## Frontend

-   React
-   TypeScript
-   Tailwind
-   TanStack Query

## Backend

-   FastAPI
-   REST APIs
-   Background workers

## Storage

-   PostgreSQL
-   pgvector
-   Redis (cache/queue)
-   S3/MinIO (artifacts)

## Integrations

-   GitHub
-   Jira
-   GitHub Actions
-   Slack (future)

### Phase 6A GitHub ingestion

The first production data path is a read-only GitHub adapter. It fetches
repositories, pull requests, and GitHub Actions workflow runs through an
injected HTTP client, maps them to the normalized `Repository`,
`PullRequest`, and `Build` entities, and persists them through an
organization-scoped synchronization service. The dashboard API remains the
only frontend contract; provider payloads do not cross that boundary.

Synchronization is bounded and idempotent. GitHub credentials are supplied
through environment configuration and are not stored in PostgreSQL. Webhooks,
background workers, Jira, and AI processing remain later subphases.

For local development, the credential is a short-lived fine-grained personal
access token limited to selected repositories with metadata, pull-request, and
Actions read-only permissions. The current adapter uses `/user/repos`, which
limits synchronization to repositories visible to that token's user. This is
deliberately not the final multi-organization design: production should use a
GitHub App installation with explicit repository selection, encrypted
credentials, and organization approval where required.

### Phase 6B Jira ingestion

The Jira adapter follows the same provider-isolation boundary as GitHub. A
read-only client fetches only explicitly configured projects, maps issues,
epics, versions/releases, and optional sprint data into normalized entities,
and persists them through an organization-scoped idempotent synchronization
service.

Local development uses a dedicated Jira service account with an API token
provided through environment configuration. Production should use Atlassian
OAuth or an equivalent centrally managed credential flow with encryption,
rotation, project scoping, and audit logging.

## AI Components

-   LiteLLM gateway
-   Embeddings
-   Risk scoring service
-   Summary generation service

## AI Agents

-   GitHub Agent
-   Jira Agent
-   Risk Agent
-   Summary Agent
-   Chat Agent

Each agent defines Inputs, Processing, Outputs and Confidence.

## Core Tables

Organization, User, Repository, PullRequest, Commit, Issue, Sprint,
Build, Deployment, AISummary, Risk.

## Directory Structure

```
engineering-intelligence/
│
├── docs/
│   ├── PLAN.md
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── MILESTONES.md
│   ├── API_SPEC.md
│   ├── DATABASE.md
│   ├── AI_AGENTS.md
│   ├── PROMPTS.md
│   ├── ROADMAP.md
│   └── DECISIONS/
│
├── frontend/
├── backend/
├── workers/
├── infrastructure/
├── docker/
└── scripts/
```
