import logging
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import create_engine_from_url, session_scope
from app.models import Organization
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_session() -> Iterator[Session]:
    settings = get_settings()
    if settings.database_url is None:
        logger.error("Dashboard overview requested without DATABASE_URL configured.")
        raise HTTPException(status_code=500, detail="Dashboard overview is unavailable.")

    engine = create_engine_from_url(settings.database_url)
    try:
        with session_scope(engine) as session:
            yield session
    finally:
        engine.dispose()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    session: Annotated[Session, Depends(get_dashboard_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DashboardOverview:
    try:
        organization_id = session.scalar(
            select(Organization.id).where(
                Organization.name == settings.default_organization_name
            )
        )
        if organization_id is None:
            raise LookupError("The configured dashboard organization does not exist.")

        return DashboardService().get_overview(session, organization_id)
    except (LookupError, SQLAlchemyError):
        logger.exception("Unable to assemble the dashboard overview.")
        raise HTTPException(
            status_code=500,
            detail="Dashboard overview is unavailable.",
        ) from None
