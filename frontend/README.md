# Engineering Intelligence Frontend

Next.js frontend for the Engineering Intelligence dashboard MVP. It renders a
shared header, KPI cards, release status, off-timeline epics, and hot
repository views from the backend dashboard overview API.

Set `BACKEND_API_BASE_URL` in `.env.local` (see `.env.example`). The value is
server-only; do not rename it to `NEXT_PUBLIC_*`. While the overview request
is pending, unavailable, or has no source data, the dashboard renders explicit
loading, error, or empty states instead of production mock data.

## Commands

```bash
npm run dev
npm run lint
npm run test
npm run test:e2e
npm run build
```

The browser suite starts two local Next.js instances and deterministic backend
stubs. It verifies live overview rendering, the profile menu, and the explicit
backend-error state without external credentials. For a real seeded check,
start the backend with migrations applied and `uv run python -m app.seed`, then
start the frontend with `BACKEND_API_BASE_URL` set to the backend URL.
