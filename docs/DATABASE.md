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
