# AI Engineering Intelligence Platform

## Starting Point

The initial scaffolding for frontend and backend has been created. The MVP for frontend is ready with fake data. This is not yet designed for the Docker setup. It's just basic scaffolding with respective frameworks.

## Directory Structure

```
eng-intelligence-platform/
│
├── docs/
│   ├── PLAN.md
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   ├── DATABASE.md
│   ├── APP_AGENTS.md
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

## Project documentation

All documents for planning and executing this project will be in the docs/ directory.
Please review the docs/PLAN.md document before proceeding.

Details of available documents

- PRD.md – Detailed product requirements and user stories.
- ARCHITECTURE.md – System architecture, services, APIs, database schema, and agent design.
- DATABASE.md — Complete PostgreSQL schema with indexes, relationships, and migrations.
- API_SPEC.md — REST API contracts (or OpenAPI) so frontend and backend can evolve independently.
- APP_AGENTS.md — Responsibilities, inputs, outputs, prompts, and orchestration for each AI agent.
- PROMPTS.md — Version-controlled system prompts and prompt templates. This becomes invaluable as the product evolves.
- ROADMAP.md — A product roadmap from MVP to an enterprise-ready Engineering Intelligence Platform.
- PLAN.md - Detailed product development plan with sub checklists and success criteria.
