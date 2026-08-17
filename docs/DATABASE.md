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
