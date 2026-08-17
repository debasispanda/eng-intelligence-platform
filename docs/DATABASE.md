# Database Design

## Core Entities

-   Organization
-   User
-   Team
-   Repository
-   PullRequest
-   Commit
-   Issue
-   Sprint
-   Build
-   Deployment
-   AISummary
-   Risk
-   Notification
-   IngestionRun

## Principles

-   UUID primary keys
-   Audit timestamps
-   Foreign keys and indexes.

## Test Isolation

Persistence tests use a generated, temporary PostgreSQL schema with
SQLAlchemy schema translation. The schema is dropped after each test, so tests
do not write to the current `public` application tables. The configured
development database role must be able to create and drop schemas.

## Dashboard Source Mapping

The first dashboard persists normalized records rather than raw GitHub, Jira,
or CI payloads. Phase 6A starts with read-only GitHub synchronization; adapters
translate provider payloads into the following model and never expose raw
provider response shapes through the dashboard API.

| Normalized entity | Future source | Identity and mapping |
| --- | --- | --- |
| `Organization` / `User` | Platform configuration or identity provider | One development organization and its first user provide the unauthenticated dashboard scope and profile. |
| `Repository` | GitHub repository | `provider_id` stores the immutable provider repository identifier; `full_name` is the display name. |
| `PullRequest` | GitHub pull request | Store repository, number, state, opened time, and merged time. The dashboard derives open, merged, and activity metrics from these values. |
| `Build` | GitHub Actions or CI provider run | Store repository, final status, start time, and completion time. Failed-build metrics use completed failed runs. |
| `Issue` | Jira issue | `provider_id` stores the provider issue identifier; `status` is normalized to dashboard states such as `blocked`. |
| `Release` | Jira release or deployment planning source | Store organization-level owner, delivery status, completion percentage, and target date. |
| `Epic` | Jira epic and later risk analysis | Store organization-level owner, schedule delay, and normalized risk. A separate risk history model remains deferred. |

GitHub synchronization uses the provider's immutable repository, pull request,
and workflow-run identifiers for idempotency. Tokens remain in environment
configuration and are never persisted with normalized records. Synchronization
is organization-scoped and uses bounded pages so rate limits and partial
failures are explicit.

Development authentication uses a short-lived fine-grained personal access
token with repository metadata, pull-request, and Actions read-only
permissions. Production authentication is deferred to a GitHub App so
organization installations, repository selection, credential encryption, and
rotation can be managed independently of normalized data storage.

Jira development synchronization uses a dedicated read-only service account,
Jira site URL, account email, and API token. The configured project allowlist
controls synchronization scope. Required access is limited to browsing
projects, viewing issues and fields, and optionally viewing boards/sprints and
versions/releases. Jira credentials are never stored in normalized records;
production credential management is deferred to OAuth or an equivalent
centrally managed integration.

Jira normalization currently uses these explicit defaults: issue status maps
`Blocked`/`Impediment` to `blocked`, completed statuses to `done`, and other
statuses to `open`. For epics, the Jira `Change risk` field
(`customfield_10006`) is authoritative when present. If it is empty,
`risk-high` and `risk-medium` labels are used; otherwise risk is derived from
delay: `0` days is `Low`, `1-7` days is `Medium`, and `8+` days is `High`.
Delay is calculated as the non-negative difference between the UTC
synchronization date and Jira `duedate`. The legacy `delay-days:N` label
remains supported as an explicit delay override. Jira versions map to releases with completion derived from
issues linked through `fixVersion`: completed issues divided by all linked
issues, rounded to the nearest integer percentage. Released versions are
forced to `100%`; versions without linked issues remain `0%`. Released
versions are `On Track`; unreleased versions with a past target date are
`Delayed`, versions due within seven days are `At Risk`, and later versions
are `On Track`. Versions without a target or start date are skipped.
Sprint/board data is deferred until a normalized sprint model is added.

`IngestionRun` records provider synchronization lifecycle without storing
tokens or raw provider payloads. Its status is `running`, `succeeded`, or
`failed`; retries increment `attempt_count`, and failures store only a
sanitized error message.

Dashboard aggregation evaluates timestamps against the request-time UTC clock:

- **Open PRs** is the current count with `state = open`; its weekly delta is
  newly opened PRs in the last seven days minus the preceding seven days.
- **Merged PRs** and **Failed Builds** are seven-day counts; each delta
  compares the same preceding seven-day period.
- **Blocked Tickets** is the current blocked-issue count; its delta compares
  newly blocked issues created in the last 24 hours with the preceding 24
  hours.
- Hot repositories rank the top four repositories by PRs opened in the last
  seven days and by failed completed builds in the last seven days,
  respectively. Ties use repository name ascending.
- Releases order by target date ascending. Off-timeline epics exclude
  zero-delay records and order by delay descending, then title ascending.
