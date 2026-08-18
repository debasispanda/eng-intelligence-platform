from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Epic, Release
from app.schemas.dashboard import RiskAssessment

RISK_RULE_VERSION = "risk-v1"


class RiskScoringService:
    def assess(self, session: Session, organization_id: UUID) -> list[RiskAssessment]:
        assessments = [
            *(
                self._assess_epic(epic)
                for epic in session.scalars(
                    select(Epic)
                    .where(Epic.organization_id == organization_id)
                    .order_by(Epic.title, Epic.id)
                ).all()
            ),
            *(
                self._assess_release(release)
                for release in session.scalars(
                    select(Release)
                    .where(Release.organization_id == organization_id)
                    .order_by(Release.target_date, Release.name, Release.id)
                ).all()
            ),
        ]
        return sorted(assessments, key=lambda item: (-item.score, item.title, item.entity_id))

    @staticmethod
    def _assess_epic(epic: Epic) -> RiskAssessment:
        base_score = {"Low": 20, "Medium": 55, "High": 85}[epic.risk]
        delay_score = min(15, epic.delayed_by_days * 2)
        score = min(100, base_score + delay_score)
        factors = [f"Source risk is {epic.risk}."]
        if epic.delayed_by_days:
            factors.append(f"Schedule delay is {epic.delayed_by_days} day(s).")
        return RiskAssessment(
            entity_type="epic",
            entity_id=str(epic.id),
            title=epic.title,
            risk=_risk_level(score),
            score=score,
            confidence=0.95,
            rule_version=RISK_RULE_VERSION,
            factors=factors,
        )

    @staticmethod
    def _assess_release(release: Release) -> RiskAssessment:
        status_score = {"On Track": 15, "At Risk": 55, "Delayed": 85}[release.status]
        incomplete_score = round((100 - release.completion) * 0.2)
        score = min(100, status_score + incomplete_score)
        factors = [
            f"Release status is {release.status}.",
            f"Completion is {release.completion}%.",
        ]
        return RiskAssessment(
            entity_type="release",
            entity_id=str(release.id),
            title=release.name,
            risk=_risk_level(score),
            score=score,
            confidence=0.9,
            rule_version=RISK_RULE_VERSION,
            factors=factors,
        )


def _risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"
