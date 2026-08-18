from datetime import UTC, date, datetime, timedelta

from app.models import Build, Epic, Organization, PullRequest, Release, Repository
from app.services.risk import RiskScoringService


def test_risk_scoring_returns_explainable_sorted_assessments(db_session) -> None:
    organization = Organization(name="Risk Test")
    db_session.add(organization)
    db_session.flush()
    db_session.add_all(
        [
            Epic(
                organization_id=organization.id,
                title="Delayed epic",
                owner="Platform",
                delayed_by_days=8,
                risk="Medium",
            ),
            Release(
                organization_id=organization.id,
                name="At-risk release",
                owner="Platform",
                status="At Risk",
                completion=25,
                target_date=date(2026, 9, 1),
            ),
            Release(
                organization_id=organization.id,
                name="On-track release",
                owner="Platform",
                status="On Track",
                completion=90,
                target_date=date(2026, 9, 2),
            ),
        ]
    )
    repository = Repository(
        organization_id=organization.id,
        provider_id="repo-1",
        full_name="platform",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.flush()
    db_session.add_all(
        [
            PullRequest(
                repository_id=repository.id,
                number=1,
                state="open",
                opened_at=datetime.now(UTC),
            ),
            Build(
                repository_id=repository.id,
                status="failed",
                started_at=datetime.now(UTC) - timedelta(hours=1),
                completed_at=datetime.now(UTC),
            ),
        ]
    )
    db_session.commit()

    assessments = RiskScoringService().assess(db_session, organization.id)

    assert [assessment.title for assessment in assessments] == [
        "At-risk release",
        "Delayed epic",
        "On-track release",
    ]
    assert assessments[0].risk == "High"
    assert assessments[1].rule_version == "risk-v2"
    assert assessments[1].confidence == 0.9
    assert assessments[1].factors == [
        "Source risk is Medium.",
        "Schedule delay is 8 day(s).",
        "1 build failure(s) occurred in the last 7 days.",
        "1 pull request(s) are currently open.",
    ]
