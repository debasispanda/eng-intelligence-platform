from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Build, Epic, Issue, PullRequest, Release, Repository
from app.schemas.dashboard import RiskAssessment

RISK_RULE_VERSION = "risk-v2"


class RiskScoringService:
    def assess(self, session: Session, organization_id: UUID) -> list[RiskAssessment]:
        signals = self._organization_signals(session, organization_id)
        assessments = [
            *(
                self._assess_epic(epic, signals)
                for epic in session.scalars(
                    select(Epic)
                    .where(Epic.organization_id == organization_id)
                    .order_by(Epic.title, Epic.id)
                ).all()
            ),
            *(
                self._assess_release(release, signals)
                for release in session.scalars(
                    select(Release)
                    .where(Release.organization_id == organization_id)
                    .order_by(Release.target_date, Release.name, Release.id)
                ).all()
            ),
        ]
        return sorted(assessments, key=lambda item: (-item.score, item.title, item.entity_id))

    @staticmethod
    def _organization_signals(session: Session, organization_id: UUID) -> dict[str, int]:
        week_ago = datetime.now(UTC) - timedelta(days=7)
        blocked_issues = session.scalar(
            select(func.count(Issue.id)).where(
                Issue.organization_id == organization_id,
                Issue.status == "blocked",
            )
        ) or 0
        failed_builds = session.scalar(
            select(func.count(Build.id))
            .join(Repository, Build.repository_id == Repository.id)
            .where(
                Repository.organization_id == organization_id,
                Build.status == "failed",
                Build.completed_at >= week_ago,
            )
        ) or 0
        open_pull_requests = session.scalar(
            select(func.count(PullRequest.id))
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(
                Repository.organization_id == organization_id,
                PullRequest.state == "open",
            )
        ) or 0
        return {
            "blocked_issues": blocked_issues,
            "failed_builds": failed_builds,
            "open_pull_requests": open_pull_requests,
        }

    @staticmethod
    def _pressure_points(signals: dict[str, int]) -> tuple[int, list[str]]:
        points = min(5, signals["blocked_issues"]) + min(5, signals["failed_builds"])
        points += min(5, signals["open_pull_requests"] // 5)
        factors: list[str] = []
        if signals["blocked_issues"]:
            factors.append(f"{signals['blocked_issues']} blocked issue(s) affect the organization.")
        if signals["failed_builds"]:
            factors.append(f"{signals['failed_builds']} build failure(s) occurred in the last 7 days.")
        if signals["open_pull_requests"]:
            factors.append(f"{signals['open_pull_requests']} pull request(s) are currently open.")
        return points, factors

    @staticmethod
    def _assess_epic(epic: Epic, signals: dict[str, int]) -> RiskAssessment:
        base_score = {"Low": 20, "Medium": 55, "High": 85}[epic.risk]
        delay_score = min(15, epic.delayed_by_days * 2)
        pressure_score, pressure_factors = RiskScoringService._pressure_points(signals)
        score = min(100, base_score + delay_score + pressure_score)
        factors = [f"Source risk is {epic.risk}."]
        if epic.delayed_by_days:
            factors.append(f"Schedule delay is {epic.delayed_by_days} day(s).")
        factors.extend(pressure_factors)
        return RiskAssessment(
            entity_type="epic",
            entity_id=str(epic.id),
            title=epic.title,
            risk=_risk_level(score),
            score=score,
            confidence=0.9,
            rule_version=RISK_RULE_VERSION,
            factors=factors,
        )

    @staticmethod
    def _assess_release(release: Release, signals: dict[str, int]) -> RiskAssessment:
        status_score = {"On Track": 15, "At Risk": 55, "Delayed": 85}[release.status]
        incomplete_score = round((100 - release.completion) * 0.2)
        pressure_score, pressure_factors = RiskScoringService._pressure_points(signals)
        score = min(100, status_score + incomplete_score + pressure_score)
        factors = [
            f"Release status is {release.status}.",
            f"Completion is {release.completion}%.",
        ]
        factors.extend(pressure_factors)
        return RiskAssessment(
            entity_type="release",
            entity_id=str(release.id),
            title=release.name,
            risk=_risk_level(score),
            score=score,
            confidence=0.85,
            rule_version=RISK_RULE_VERSION,
            factors=factors,
        )


def _risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"
