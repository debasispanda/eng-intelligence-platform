from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Organization, Repository


def test_database_session_uses_an_isolated_schema(db_session: Session) -> None:
    organization = Organization(name="Fixture Organization")
    db_session.add(organization)
    db_session.commit()

    persisted_organization = db_session.scalar(
        select(Organization).where(Organization.id == organization.id)
    )

    assert persisted_organization is not None
    assert persisted_organization.name == "Fixture Organization"


def test_database_foreign_key_constraints_are_enforced(db_session: Session) -> None:
    db_session.add(
        Repository(
            organization_id=uuid4(),
            provider_id="missing:organization",
            full_name="missing-organization",
            default_branch="main",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
