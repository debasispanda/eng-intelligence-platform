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
  development default organization. Authentication and organization selection
  will replace this temporary scope in a later phase.

## Auth

-   POST /auth/login
-   POST /auth/logout

## GitHub

-   POST /integrations/github/connect
-   POST /webhooks/github

## Jira

-   POST /integrations/jira/connect

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

#### Errors

| Status | Response | When |
| --- | --- | --- |
| `500` | `{ "detail": "Dashboard overview is unavailable." }` | The overview cannot be assembled because of an unexpected server or persistence failure. |

## AI

-   GET /summaries/daily
-   GET /risks
-   POST /chat
