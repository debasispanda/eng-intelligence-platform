# Engineering Intelligence Platform

## Repository workflow

- Read `docs/PLAN.md` before planning or implementing work. Treat the documents in `docs/` as the source of truth for product requirements, API contracts, data model, agent responsibilities, prompts, and roadmap.
- The repository currently contains independent frontend and backend scaffolds; it is not Dockerized.
- Preserve unrelated work already present in the worktree.
- For every planned item, implement the change first, run the relevant focused
  tests and validation commands, inspect the results, and only then mark the
  item complete in `docs/PLAN.md` or the session task tracker. Never mark work
  complete before its validation passes.

## Commands

Run frontend commands from `frontend/`:

```bash
npm run dev
npm run lint
npm run test
npm run test -- app/page.test.tsx
npm run test -- components/header/app-header.test.tsx
npm run build
```

The backend is a Python 3.12+ FastAPI project managed with `uv` (`backend/pyproject.toml` and `backend/uv.lock`). No backend test or lint command is configured yet. Its current application can be run with:

```bash
cd backend && uv run fastapi dev app/main.py
```

## Current architecture

- `frontend/` is a Next.js 16 App Router dashboard MVP using React 19, TypeScript, Tailwind CSS 4, and Vitest with React Testing Library. `app/layout.tsx` is the shared server-rendered shell and mounts `AppHeader` for every route. Keep browser-only state isolated to client components, as `components/header/user-menu.tsx` does.
- The dashboard page is deliberately API-free for now. All display data and its TypeScript contracts are centralized in `frontend/lib/dashboard-data.ts`; use it as the replacement seam when wiring real dashboard APIs. The page composes reusable `StatCard`, `SectionCard`, and `StatusBadge` primitives.
- `backend/app/main.py` is only a minimal FastAPI scaffold. The documented target system is FastAPI REST APIs, PostgreSQL with pgvector, Redis-backed workers/cache, object storage, realtime updates, LiteLLM, and GitHub/Jira integrations. Keep API work aligned with `docs/API_SPEC.md`, schema work aligned with `docs/DATABASE.md`, and AI work aligned with `docs/AI_AGENTS.md` and `docs/PROMPTS.md`.

## Frontend conventions

- Follow the locked MVP dashboard shape: KPI strip, release status plus off-timeline epics, then the two hot-repository lists. The header remains global; the profile menu and Sign out are presentation-only placeholders with no authentication.
- Keep mock dashboard data strongly typed and centralized. New data shapes should be exported types in `lib/dashboard-data.ts` and use `satisfies` on fixture collections.
- Use the `@/*` import alias. TypeScript is strict, and tests import `describe`, `it`, and `expect` explicitly from Vitest; `frontend/test/setup.ts` supplies `jest-dom` matchers.
- Build the existing black/light-gray visual system from the custom CSS tokens in `app/globals.css`. It follows `prefers-color-scheme`; preserve light and dark behavior when adding UI.
- This project uses a newer Next.js version with breaking changes. Before changing Next.js-specific behavior, consult the relevant documentation under `frontend/node_modules/next/dist/docs/` and heed deprecation notices.
