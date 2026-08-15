from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_engine_from_url, session_scope
from app.models import (
    Build,
    Epic,
    Issue,
    Organization,
    PullRequest,
    Release,
    Repository,
    User,
)

DEMO_ORGANIZATION_NAME = "Engineering Intelligence Demo"
SEED_TIME = datetime(2026, 8, 15, 12, tzinfo=UTC)


def seed_dashboard_data(session: Session) -> Organization:
    organization = session.scalar(
        select(Organization).where(Organization.name == DEMO_ORGANIZATION_NAME)
    )
    if organization is not None:
        return organization

    organization = Organization(name=DEMO_ORGANIZATION_NAME)
    session.add(organization)
    session.flush()

    session.add(
        User(
            organization_id=organization.id,
            name="Riley Chen",
            role="VP Engineering",
            email="riley.chen@example.com",
            avatar_initials="RC",
        )
    )
    repositories = {
        name: Repository(
            organization_id=organization.id,
            provider_id=f"demo:{name}",
            full_name=name,
            default_branch="main",
        )
        for name in ("frontend-app", "platform-api", "event-router", "data-sync", "mobile-sdk")
    }
    session.add_all(repositories.values())
    session.flush()

    _seed_pull_requests(session, repositories)
    _seed_builds(session, repositories)
    session.add_all(
        [
            Issue(
                organization_id=organization.id,
                provider_id=f"demo:issue:{number}",
                title=title,
                status="blocked",
                created_at=SEED_TIME - age,
            )
            for number, title, age in (
                (1, "Resolve cross-region deployment failure", timedelta(hours=8)),
                (2, "Upgrade tenant isolation migration", timedelta(hours=16)),
                (3, "Unblock metrics pipeline backfill", timedelta(days=1, hours=4)),
                (4, "Verify mobile release signing", timedelta(days=3)),
            )
        ]
    )
    session.add_all(
        [
            Release(
                organization_id=organization.id,
                name=name,
                owner=owner,
                status=status,
                completion=completion,
                target_date=target_date,
            )
            for name, owner, status, completion, target_date in (
                ("Platform 2.8", "Core Services", "On Track", 74, SEED_TIME.date() - timedelta(days=11)),
                ("Web App 5.2", "Frontend", "At Risk", 58, SEED_TIME.date() - timedelta(days=18)),
                ("Data Sync 1.9", "Data Platform", "Delayed", 41, SEED_TIME.date() - timedelta(days=4)),
                ("Mobile SDK 3.3", "Developer Experience", "On Track", 67, SEED_TIME.date() - timedelta(days=7)),
            )
        ]
    )
    session.add_all(
        [
            Epic(
                organization_id=organization.id,
                title=title,
                owner=owner,
                delayed_by_days=delay,
                risk=risk,
            )
            for title, owner, delay, risk in (
                ("Tenant Isolation Upgrade", "Platform Security", 9, "High"),
                ("Unified Metrics Pipeline", "Data Platform", 6, "Medium"),
                ("Checkout Latency Program", "Growth Engineering", 4, "Medium"),
                ("Observability Coverage", "SRE", 2, "Low"),
            )
        ]
    )
    session.flush()
    return organization


def _seed_pull_requests(session: Session, repositories: dict[str, Repository]) -> None:
    number = 1
    for repository_name, open_count, merged_count in (
        ("frontend-app", 3, 4),
        ("platform-api", 2, 3),
        ("event-router", 2, 2),
        ("data-sync", 1, 2),
        ("mobile-sdk", 0, 1),
    ):
        repository = repositories[repository_name]
        for index in range(open_count):
            session.add(
                PullRequest(
                    repository_id=repository.id,
                    number=number,
                    state="open",
                    opened_at=SEED_TIME - timedelta(days=index + 1),
                )
            )
            number += 1
        for index in range(merged_count):
            opened_at = SEED_TIME - timedelta(days=index + 3)
            session.add(
                PullRequest(
                    repository_id=repository.id,
                    number=number,
                    state="merged",
                    opened_at=opened_at,
                    merged_at=opened_at + timedelta(hours=12),
                )
            )
            number += 1


def _seed_builds(session: Session, repositories: dict[str, Repository]) -> None:
    for repository_name, failed_count in (
        ("platform-api", 3),
        ("mobile-sdk", 2),
        ("data-sync", 1),
        ("frontend-app", 1),
        ("event-router", 0),
    ):
        repository = repositories[repository_name]
        for index in range(failed_count):
            completed_at = SEED_TIME - timedelta(days=index + 1)
            session.add(
                Build(
                    repository_id=repository.id,
                    status="failed",
                    started_at=completed_at - timedelta(minutes=10),
                    completed_at=completed_at,
                )
            )


def main() -> None:
    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required to seed dashboard data.")

    engine = create_engine_from_url(settings.database_url)
    try:
        with session_scope(engine) as session:
            seed_dashboard_data(session)
            session.commit()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
