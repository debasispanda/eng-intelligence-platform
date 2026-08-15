from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

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
from app.services.dashboard import DashboardService

NOW = datetime(2026, 8, 15, 12, tzinfo=UTC)


def test_dashboard_service_aggregates_only_the_requested_organization(db_session: Session) -> None:
    organization = Organization(name="Dashboard Organization")
    other_organization = Organization(name="Other Organization")
    db_session.add_all([organization, other_organization])
    db_session.flush()

    db_session.add(
        User(
            organization_id=organization.id,
            name="Riley Chen",
            role="VP Engineering",
            email="riley@example.com",
            avatar_initials="RC",
        )
    )
    repository = Repository(
        organization_id=organization.id,
        provider_id="dashboard:repo",
        full_name="dashboard-repo",
        default_branch="main",
    )
    other_repository = Repository(
        organization_id=other_organization.id,
        provider_id="other:repo",
        full_name="other-repo",
        default_branch="main",
    )
    db_session.add_all([repository, other_repository])
    db_session.flush()

    db_session.add_all(
        [
            PullRequest(
                repository_id=repository.id,
                number=1,
                state="open",
                opened_at=NOW - timedelta(days=1),
            ),
            PullRequest(
                repository_id=repository.id,
                number=2,
                state="open",
                opened_at=NOW - timedelta(days=2),
            ),
            PullRequest(
                repository_id=repository.id,
                number=3,
                state="merged",
                opened_at=NOW - timedelta(days=3),
                merged_at=NOW - timedelta(days=2),
            ),
            PullRequest(
                repository_id=repository.id,
                number=4,
                state="merged",
                opened_at=NOW - timedelta(days=4),
                merged_at=NOW - timedelta(days=3),
            ),
            PullRequest(
                repository_id=repository.id,
                number=5,
                state="merged",
                opened_at=NOW - timedelta(days=10),
                merged_at=NOW - timedelta(days=10),
            ),
            PullRequest(
                repository_id=other_repository.id,
                number=1,
                state="open",
                opened_at=NOW - timedelta(days=1),
            ),
            Build(
                repository_id=repository.id,
                status="failed",
                started_at=NOW - timedelta(days=1, minutes=5),
                completed_at=NOW - timedelta(days=1),
            ),
            Build(
                repository_id=repository.id,
                status="failed",
                started_at=NOW - timedelta(days=10, minutes=5),
                completed_at=NOW - timedelta(days=10),
            ),
            Build(
                repository_id=other_repository.id,
                status="failed",
                started_at=NOW - timedelta(days=1, minutes=5),
                completed_at=NOW - timedelta(days=1),
            ),
            Issue(
                organization_id=organization.id,
                provider_id="dashboard:issue:1",
                title="Current blocked issue",
                status="blocked",
                created_at=NOW - timedelta(hours=12),
            ),
            Issue(
                organization_id=organization.id,
                provider_id="dashboard:issue:2",
                title="Previous blocked issue",
                status="blocked",
                created_at=NOW - timedelta(hours=36),
            ),
            Release(
                organization_id=organization.id,
                name="Later Release",
                owner="Platform",
                status="On Track",
                completion=50,
                target_date=NOW.date() + timedelta(days=2),
            ),
            Release(
                organization_id=organization.id,
                name="Earlier Release",
                owner="Platform",
                status="At Risk",
                completion=25,
                target_date=NOW.date() + timedelta(days=1),
            ),
            Epic(
                organization_id=organization.id,
                title="Delayed Epic",
                owner="Platform",
                delayed_by_days=3,
                risk="High",
            ),
            Epic(
                organization_id=organization.id,
                title="On time Epic",
                owner="Platform",
                delayed_by_days=0,
                risk="Low",
            ),
        ]
    )
    db_session.commit()

    overview = DashboardService().get_overview(db_session, organization.id, now=NOW)

    assert [(kpi.title, kpi.value, kpi.delta, kpi.trend) for kpi in overview.kpis] == [
        ("Open PRs", "2", "+3 this week", "up"),
        ("Merged PRs", "2", "+1 this week", "up"),
        ("Failed Builds", "1", "+0 since last week", "flat"),
        ("Blocked Tickets", "2", "+0 since yesterday", "flat"),
    ]
    assert [release.name for release in overview.releases] == ["Earlier Release", "Later Release"]
    assert [epic.epic for epic in overview.off_timeline_epics] == ["Delayed Epic"]
    assert overview.hot_repositories.most_active[0].repository == "dashboard-repo"
    assert overview.hot_repositories.most_active[0].metric == 4
    assert overview.hot_repositories.most_failed[0].metric == 1


def test_dashboard_service_returns_empty_sections_for_an_organization_without_data(
    db_session: Session,
) -> None:
    organization = Organization(name="Empty Organization")
    db_session.add(organization)
    db_session.flush()
    db_session.add(
        User(
            organization_id=organization.id,
            name="Riley Chen",
            role="VP Engineering",
            email="empty@example.com",
            avatar_initials="RC",
        )
    )
    db_session.commit()

    overview = DashboardService().get_overview(db_session, organization.id, now=NOW)

    assert overview.kpis == []
    assert overview.releases == []
    assert overview.off_timeline_epics == []
    assert overview.hot_repositories.most_active == []
    assert overview.hot_repositories.most_failed == []
