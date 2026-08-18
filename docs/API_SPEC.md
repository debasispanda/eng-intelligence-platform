# API Specification

## Conventions

- API responses use JSON with `Content-Type: application/json`.
- Field names use lower camel case.
- Timestamps use RFC 3339 UTC strings. Dashboard target dates use ISO 8601
  calendar dates (`YYYY-MM-DD`).
- Resource identifiers are UUID strings once persistence is introduced.
- Successful collection fields are arrays, including when no records exist.
- Error responses use `{ "detail": "<human-readable message>" }`. Validation
  failures follow FastAPI's standard `422` response shape.
- The initial connected dashboard is unauthenticated and serves the
  `DEFAULT_ORGANIZATION_NAME` development organization, which defaults to
  `Engineering Intelligence Demo`. Authentication and organization selection
  will replace this temporary scope in a later phase.
- The Next.js server reads `BACKEND_API_BASE_URL` to reach the backend. Keep
  this value server-only; do not use a `NEXT_PUBLIC_` variable for the
  dashboard overview request.

## Auth

-   POST /auth/login
-   POST /auth/logout

## Health

### `GET /health`

Returns `{"status":"ok"}` when the API process is running.

### `GET /health/redis`

Checks connectivity from the API process to the platform-managed Redis
instance. It returns `200` with `{"status":"ok"}` when Redis is reachable and
`503` with `{"detail":"Redis is unavailable."}` otherwise.

## GitHub

-   POST /integrations/github/connect
-   POST /webhooks/github

The current Phase 6A development synchronization is command-based rather than
an HTTP endpoint. It uses a fine-grained GitHub personal access token with
`Metadata: Read-only`, `Pull requests: Read-only`, and `Actions: Read-only`
permissions. The token is supplied through `GITHUB_TOKEN` and is never
returned by the API or persisted in normalized database records.

The development client reads `/user/repos`, so it is limited to repositories
visible to the authenticated user. A future production integration will use a
GitHub App installation to support explicit organization/repository selection,
encrypted credentials, and webhook synchronization.

## Jira

-   POST /integrations/jira/connect

### Phase 6B development synchronization

The initial Jira integration is a command-based, read-only synchronization
rather than a public HTTP endpoint. Configure the Jira site URL, account email,
and API token through environment variables. The token must not be returned by
the API or persisted in normalized database records.

The development integration should use a dedicated Jira service account with
the minimum read permissions required for the selected projects:

- Browse projects and view project details.
- Browse issues and view issue fields.
- View sprints and boards when sprint data is enabled.
- View releases/versions when release data is enabled.

The first synchronization scope is explicitly selected Jira projects. It maps
issues to `Issue`, epics to `Epic`, versions/releases to `Release`, and sprint
dates/status to the corresponding normalized delivery fields. Raw Jira
payloads do not cross the dashboard API boundary.

For epics, `Change risk` is used when present. Otherwise risk labels are used,
then risk is derived from due-date delay: `0` days is `Low`, `1-7` days is
`Medium`, and `8+` days is `High`. Delay is calculated against the UTC
synchronization date.

For Jira versions, released versions are `On Track` with `100%` completion.
Unreleased versions with a past target date are `Delayed`, versions due within
seven days are `At Risk`, and later versions are `On Track`. Unreleased
versions derive completion from the ratio of done issues to all issues linked
through `fixVersion`; versions without linked issues return `0%`.

For production, replace the development API-token flow with an Atlassian OAuth
integration or centrally managed service account, including encrypted
credential storage, project selection, rotation, and audit logging.

## Dashboard

### `GET /dashboard/overview`

Returns all data needed to render the dashboard and global application header.
The endpoint has no query parameters in the initial implementation.

#### Response `200 OK`

```json
{
  "appTitle": "Engineering Intelligence",
  "profile": {
    "name": "Riley Chen",
    "role": "VP Engineering",
    "email": "riley.chen@example.com",
    "avatarInitials": "RC"
  },
  "kpis": [
    {
      "title": "Open PRs",
      "value": "38",
      "delta": "+6 this week",
      "trend": "up"
    }
  ],
  "releases": [
    {
      "name": "Platform 2.8",
      "owner": "Core Services",
      "status": "On Track",
      "completion": 74,
      "date": "2026-08-04"
    }
  ],
  "offTimelineEpics": [
    {
      "epic": "Tenant Isolation Upgrade",
      "owner": "Platform Security",
      "delayedByDays": 9,
      "risk": "High"
    }
  ],
  "hotRepositories": {
    "mostActive": [
      {
        "repository": "frontend-app",
        "metric": 36,
        "label": "PRs this week"
      }
    ],
    "mostFailed": [
      {
        "repository": "platform-api",
        "metric": 7,
        "label": "failed builds"
      }
    ]
  }
}
```

#### Field constraints

| Field | Type | Constraints |
| --- | --- | --- |
| `profile.avatarInitials` | string | Short display label for the avatar. |
| `kpis[].trend` | string | `up`, `down`, or `flat`. |
| `releases[].status` | string | `On Track`, `At Risk`, or `Delayed`. |
| `releases[].completion` | integer | Percentage from `0` through `100`. |
| `offTimelineEpics[].delayedByDays` | integer | Non-negative number of days behind plan. |
| `offTimelineEpics[].risk` | string | `Low`, `Medium`, or `High`. |
| `hotRepositories.*[].metric` | integer | Non-negative ranked metric. |

Empty data is represented by empty `kpis`, `releases`, `offTimelineEpics`,
`mostActive`, and `mostFailed` arrays. The response still includes `appTitle`
and `profile`.

Metric calculation windows, ranking limits, and deterministic ordering are
defined in `docs/DATABASE.md` under **Dashboard Source Mapping**.

#### Errors

| Status | Response | When |
| --- | --- | --- |
| `500` | `{ "detail": "Dashboard overview is unavailable." }` | The overview cannot be assembled because of an unexpected server or persistence failure. |

### `GET /dashboard/ingestion-runs`

Returns the latest organization-scoped GitHub and Jira synchronization runs.
The optional `limit` query parameter accepts values from 1 through 50 and
defaults to 10.

Each item contains the provider, lifecycle status, attempt count, timestamps,
record count, and a sanitized error message when the run failed.

#### Errors

| Status | Response | When |
| --- | --- | --- |
| `500` | `{ "detail": "Ingestion run history is unavailable." }` | The configured organization is missing or persistence fails. |

## AI

-   GET /summaries/daily
-   GET /risks
-   POST /chat
