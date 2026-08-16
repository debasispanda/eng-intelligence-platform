# Engineering Intelligence Platform -- Backend and Frontend Integration Plan

## Scope and sequencing

The existing Next.js dashboard remains the visual reference while its typed
mock-data boundary is replaced with an API-backed implementation. The first
end-to-end milestone is a reliable dashboard overview, not authentication,
GitHub/Jira OAuth, background workers, AI generation, or Docker deployment.
Those capabilities follow after the dashboard data path is established.

Every phase must be reviewed and accepted before the dependent phase starts.
Do not introduce a frontend dependency on an endpoint until its response
contract and failure behavior are agreed.

## Quality gates

Phase 1 establishes backend tooling. Thereafter, the expected validation
commands are:

```bash
# frontend/
npm run lint
npm run test
npm run build

# backend/
uv run ruff check .
uv run pytest
```

During development, run focused tests before the full suite:

```bash
# frontend/
npm run test -- app/page.test.tsx
npm run test -- components/header/app-header.test.tsx

# backend/
uv run pytest tests/path/to/test_file.py
uv run pytest tests/path/to/test_file.py::test_name
```

Each new backend route, database operation, and frontend API state needs
automated coverage. Keep unit tests independent of external GitHub, Jira, LLM,
and cloud services; use fakes or controlled test fixtures at those boundaries.

## Phase 0 -- Confirm MVP contract and local development decisions

### Work

- [x] Expand `docs/API_SPEC.md` with the exact `GET /dashboard/overview`
  response schema, including KPI, release, epic-risk, and hot-repository
  fields currently rendered by the dashboard.
- [x] Define date/time, identifier, pagination, empty-state, and API error
  conventions shared by the frontend and backend.
- [x] Use the platform-provided PostgreSQL instance with pgvector on port
  5432. Configure access with `DATABASE_URL`; select and document the
  migration and data-access tooling in Phase 1.
- [x] Record that authentication is deferred for the first connected dashboard
  and define the temporary organization/data-scoping approach.
- [x] Map the API response to the frontend's current
  `lib/dashboard-data.ts` types; resolve deliberate differences before
  implementation.

### Testing and validation

- [x] Review API examples against every value consumed by `app/page.tsx` and
  `app/layout.tsx`.
- [x] Validate the response schema with a backend contract test fixture and a
  TypeScript type-checking consumer.

### Success criteria

- `GET /dashboard/overview` has an approved, versioned request and response
  contract with documented error responses.
- No frontend field requires inferred or undocumented backend semantics.
- Local database and configuration decisions are reproducible by another
  developer without external integrations.

## Phase 1 -- Establish the backend application foundation

### Work

- [x] Replace the sample FastAPI endpoints with an application package
  organized around configuration, routing, domain services, and persistence.
- [x] Add environment-based settings, explicit development/test configuration,
  structured application logging, CORS restricted to the local frontend
  origin, and a health endpoint.
- [x] Add the selected database driver, migration tooling, test runner, and
  linter to `backend/pyproject.toml` and lock the dependencies with `uv`.
- [x] Create test fixtures for an isolated database and FastAPI client.
- [x] Add `backend/AGENTS.md` with the backend commands and conventions once
  the toolchain is established.

### Testing and validation

- [x] Test settings validation, health responses, CORS behavior, and router
  registration.
- [x] Run `uv run ruff check .` and `uv run pytest`.
- [x] Start the app locally and verify the health endpoint responds without
  requiring GitHub, Jira, or LLM credentials.

### Success criteria

- The backend starts from a clean environment using the documented command.
- Automated tests and linting run through `uv` and have no dependence on a
  developer's local state.
- The API exposes only intentional application routes; sample endpoints are
  removed.

## Phase 2 -- Model and persist dashboard source data

### Work

- [x] Implement initial migrations for the dashboard-relevant entities:
  organization, repository, pull request, build, issue/epic, release or
  deployment, and risk data. Follow `docs/DATABASE.md`: UUID primary keys,
  audit timestamps, foreign keys, and indexes.
- [x] Create repositories/services that calculate dashboard metrics from
  persisted records rather than returning static route-local values.
- [x] Provide an idempotent development seed path that creates a realistic
  single-organization dataset matching the current dashboard scenarios.
- [x] Define how raw integration data maps to these normalized entities, while
  leaving live GitHub/Jira synchronization for a later phase.

### Testing and validation

- [x] Test migrations against an empty database and verify upgrade paths.
- [x] Test constraints, relations, indexes where query behavior depends on
  them, and organization scoping.
- [x] Test seed idempotency and metric calculations using controlled fixtures.

### Success criteria

- [x] A fresh local database can be migrated and seeded repeatedly without
  duplicate records.
- [x] Dashboard metrics derive from persisted data and are scoped to the intended
  organization.
- [x] Database tests cover the normal, empty, and no-data-yet states.

## Deferred schema cutover -- Move application tables from `public` to `platform`

`DATABASE_SCHEMA` is now configurable. Existing tables and Alembic version
history remain in `public` until this cutover is explicitly scheduled; do not
change the active schema by setting `DATABASE_SCHEMA=platform` beforehand.

### Work

- [ ] Inventory the application tables, foreign keys, indexes, migration
  version, and any non-application objects currently in `public`.
- [ ] Confirm the `platform` schema exists, has the required owner and grants,
  and is dedicated to this application.
- [ ] Update SQLAlchemy engine setup and Alembic configuration to apply the
  configured schema search path and store Alembic version history in that
  schema.
- [ ] Create a transactional, rehearsed migration that moves all application
  tables, constraints, indexes, and Alembic state to `platform`.
- [ ] Update non-application clients, monitoring, backups, and deployment
  configuration to use `DATABASE_SCHEMA=platform`.
- [ ] Retain a tested rollback procedure before changing production
  configuration.

### Testing and validation

- [ ] Rehearse the cutover against a restored production-like database and
  verify row counts, foreign keys, indexes, and Alembic head before and after.
- [ ] Run the full backend and frontend suites with
  `DATABASE_SCHEMA=platform`.
- [ ] Verify that a rollback restores the original `public` schema state
  without data loss.

### Success criteria

- All application tables and Alembic metadata reside in `platform`; no
  application queries depend on `public`.
- Dashboard API and frontend integration pass against `platform`.
- The cutover and rollback are documented and reproducible.

## Phase 3 -- Deliver the dashboard overview API

### Work

- [x] Implement `GET /dashboard/overview` according to the approved API
  contract.
- [x] Keep response schemas separate from persistence models and return
  explicit, stable field names and value types.
- [x] Aggregate the KPI strip, release status, off-timeline epics, and both
  hot-repository rankings in a dashboard service.
- [x] Return meaningful empty results for organizations without data and
  consistent error responses for invalid requests or unavailable
  dependencies.
- [x] Document the finalized endpoint and examples in `docs/API_SPEC.md`.

### Testing and validation

- [x] Unit-test each aggregation rule, ordering rule, and risk/status mapping.
- [x] Add route-level contract tests for normal, empty, and error responses.
- [x] Run the API against the seeded database and compare the response to the
  documented example.

### Success criteria

- [x] The endpoint returns all data required by the existing dashboard in one
  documented response.
- [x] Response validation, ordering, and empty-state behavior are covered by
  automated tests.
- [x] No frontend knowledge leaks into database schema or route implementation.

## Phase 4 -- Connect the Next.js dashboard

### Work

- [x] Add a typed frontend API client and response-to-view-model mapping at the
  current mock-data seam.
- [x] Replace direct dashboard mock-data reads with the overview request while
  keeping presentation components and the global header intact.
- [x] Implement a loading state, API error state, and no-data state that
  preserve the existing polished light/dark design.
- [x] Move mock data to test fixtures or an explicit development fallback only
  if required; do not silently mask backend failures in normal use.
- [x] Configure the frontend with the backend base URL through documented
  environment configuration.

### Testing and validation

- [x] Unit-test the API mapping and each loading, error, and empty UI state.
- [x] Update existing dashboard rendering tests to use controlled API fixtures
  instead of module-level production mock data.
- [x] Run `npm run lint`, `npm run test`, and `npm run build`.

### Success criteria

- [x] With the backend running, the dashboard renders persisted overview data
  without editing frontend source code.
- [x] A backend failure is visible to the user and does not render stale data as a
  successful dashboard.
- [x] Existing header, status badge, responsive table, and theme behavior remain
  intact.

## Phase 5 -- Verify the end-to-end dashboard path

### Work

- [ ] Add an integration test environment that starts the backend with an
  isolated database and serves a seeded overview response.
- [ ] Add browser-level coverage for loading the dashboard, rendering live
  data, displaying an API failure, and opening/closing the profile menu.
- [ ] Use the configured Playwright MCP server for exploratory verification
  only; keep repeatable regression coverage in the automated test suite.
- [ ] Document local startup order, required environment variables, migration,
  seed, test, lint, and build commands in the root README and service READMEs.

### Testing and validation

- [ ] Run backend lint and tests, frontend lint, tests, and production build.
- [ ] Run the end-to-end tests against the local integration environment.
- [ ] Manually verify the dashboard in both system light and dark themes.

### Success criteria

- A developer can clone, configure, migrate, seed, start, and verify the
  connected dashboard using only repository documentation.
- The complete dashboard path passes automated backend, frontend, contract,
  and browser-level tests.
- Test data, external service credentials, and production configuration are
  never required for the local end-to-end suite.

## Phase 6 -- Add production data sources and intelligence incrementally

### Work

- [ ] Add GitHub connection, webhook verification, repository synchronization,
  and GitHub Actions ingestion following the API specification.
- [ ] Add Jira connection and sprint/issue synchronization.
- [ ] Introduce background workers and Redis for non-request ingestion and
  aggregation work.
- [ ] Add risk scoring, summaries, and the documented AI agents through the
  LiteLLM gateway. Version prompts in `docs/PROMPTS.md`.
- [ ] Add authentication, organization isolation, artifact storage, realtime
  updates, and Docker deployment after the connected dashboard is stable.

### Testing and validation

- [ ] Contract-test inbound webhooks and integration clients with recorded,
  sanitized fixtures.
- [ ] Test worker retries, idempotency, organization isolation, and degraded
  dependency behavior.
- [ ] Evaluate AI outputs against versioned fixtures and assert confidence and
  structured-output requirements rather than unbounded prose.

### Success criteria

- Each integration and AI capability can be enabled independently without
  regressing the dashboard overview path.
- External data processing is observable, idempotent, and covered by tests
  that do not call third-party production systems.
- The implementation continues to match `docs/ARCHITECTURE.md`,
  `docs/API_SPEC.md`, `docs/DATABASE.md`, `docs/AI_AGENTS.md`, and
  `docs/ROADMAP.md`.
