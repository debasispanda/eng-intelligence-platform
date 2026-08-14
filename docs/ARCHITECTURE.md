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
