from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Organization


def test_database_session_uses_an_isolated_schema(db_session: Session) -> None:
    organization = Organization(name="Fixture Organization")
    db_session.add(organization)
    db_session.commit()

    persisted_organization = db_session.scalar(
        select(Organization).where(Organization.id == organization.id)
    )

    assert persisted_organization is not None
    assert persisted_organization.name == "Fixture Organization"
