# AI Engineering Intelligence Platform
Build an AI-powered Engineering Intelligence Platform that helps engineering leaders understand delivery health, identify risks, and prioritize work by continuously analyzing engineering signals.

## Starting Point

Initial scaffolding is done with NextJS and recommended libraries. The MVP
dashboard UI, shared header, reusable components, backend overview integration,
and test scaffolding are now implemented.

## Business Requirements

- There should be a dashboard page as the default route
- The dashboard page should show a header with circular user profile image with a dropdown menu to show details. This header should be a part of layout and present in all the routes.
- Don't implement any authentication mechanism for now.
- The dashboard should show project details like Open PRs, Merged PRs, Failed Builds, Blocked Tickets, Epics not running as per timeline, Release status, Hot repositories etc.
- The priority is a slick, professional, simple black/light gray theme UI/UX with very simple features
- The app should render persisted dashboard overview data from the backend

## Confirmed MVP Decisions (Locked)

- Header is global in layout and visible on all routes.
- Header left side contains app title and a dummy logo.
- Header right side contains a circular profile avatar with dropdown.
- Dropdown shows user details and includes Sign out (placeholder only, no auth implementation).
- Theme behavior follows system preference.
- No date range selector in v1.
- Dashboard uses fixed cards for now (no dynamic resizing/reconfiguration).
- Release status is shown as per-release rows.
- Hot repositories section shows two ranked views: most active and most failed.
- Epics timeline risk is displayed as a short table (not only a single metric count).

## Agreed Implementation Shape

- Keep the first version simple and elegant with three dashboard zones:
  1. KPI strip: Open PRs, Merged PRs, Failed Builds, Blocked Tickets.
  2. Health section: per-release status rows and epics off-timeline short table.
  3. Activity section: hot repositories split into most active and most failed.
- Fetch the typed dashboard overview server-side through
  `BACKEND_API_BASE_URL`; keep test data in `test/fixtures/`, not production
  modules.
- Build small reusable UI primitives for consistency: stat card, status badge, section card, avatar menu.
- Define explicit design tokens in global styles to match the provided light/dark palette.
- Keep interactions minimal and clear; prioritize professional visual polish over feature breadth.
- Add lightweight tests for critical rendering paths in MVP (header, KPI cards, release rows, epics table).

## Current Implementation

- App Router layout is the shared shell and includes the global header on all routes.
- Dashboard data is fetched by the server-side overview client in
  `lib/dashboard-api.ts`, then shared by the global header and page through
  the dashboard provider. It reads server-only `BACKEND_API_BASE_URL`.
- Reusable UI primitives are in place for stat cards, section cards, status badges, and the avatar menu.
- The dashboard page is split into the agreed three zones and uses fixed dummy data.
- Tests use Vitest + React Testing Library with explicit Vitest imports in test files and `jest-dom` matchers in the shared test setup.
- The dashboard has explicit loading, unavailable, and no-data states; never
  silently render test fixtures after an overview request fails.

## Technical Details

- Implemented as a modern Next.js App Router app.
- Server Components are used for the layout/page shell, with client interactivity isolated to the avatar menu.
- The initial scaffolding of the Next.js app is created and the MVP UI is implemented.
- No persistence
- No user management for the MVP
- Use popular libraries
- As simple as possible but with an elegant UI

## Color Scheme

- Light Theme
  - background: #ffffff
  - foreground: #171717
  - card: #f9f9f9
  - border: #e5e5e5
- Dark Theme
  - background: #000000
  - foreground: #ffffff
  - card: #0a0a0a
  - border: #262626

## Strategy

1. Keep the guide aligned with the implemented UI, data shape, and test stack.
2. Validate changes with `eslint`, `vitest`, and `next build`.
3. Use browser testing or integration checks only when a UI behavior needs runtime verification beyond unit tests.
4. Keep the MVP simple, polished, and easy to extend with API-backed data later.

## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->
