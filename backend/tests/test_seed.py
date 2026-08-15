from sqlalchemy import func, select
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
from app.seed import seed_dashboard_data


def test_dashboard_seed_is_idempotent(db_session: Session) -> None:
    organization = seed_dashboard_data(db_session)
    db_session.commit()

    seeded_counts = {
        model.__tablename__: db_session.scalar(select(func.count(model.id)))
        for model in (Organization, User, Repository, PullRequest, Build, Issue, Release, Epic)
    }

    repeated_organization = seed_dashboard_data(db_session)
    db_session.commit()

    repeated_counts = {
        model.__tablename__: db_session.scalar(select(func.count(model.id)))
        for model in (Organization, User, Repository, PullRequest, Build, Issue, Release, Epic)
    }

    assert repeated_organization.id == organization.id
    assert seeded_counts == repeated_counts
    assert seeded_counts["organizations"] == 1
    assert seeded_counts["repositories"] == 5
