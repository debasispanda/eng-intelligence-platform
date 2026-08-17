from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.dashboard import get_dashboard_session
from app.core.config import get_settings
from app.models import IngestionRun, Organization


def _test_client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


@pytest.mark.anyio
async def test_ingestion_runs_returns_latest_runs_for_default_organization(
    app: FastAPI,
    db_session: Session,
) -> None:
    settings = get_settings()
    organization = Organization(name=settings.default_organization_name)
    other_organization = Organization(name="Other")
    db_session.add_all([organization, other_organization])
    db_session.flush()
    now = datetime.now(UTC)
    db_session.add_all(
        [
            IngestionRun(
                organization_id=organization.id,
                provider="jira",
                status="failed",
                attempt_count=3,
                started_at=now,
                finished_at=now + timedelta(seconds=2),
                records_synchronized=0,
                error_message="Jira request failed with status 503.",
            ),
            IngestionRun(
                organization_id=organization.id,
                provider="github",
                status="succeeded",
                attempt_count=1,
                started_at=now - timedelta(minutes=1),
                finished_at=now - timedelta(minutes=1) + timedelta(seconds=1),
                records_synchronized=12,
            ),
            IngestionRun(
                organization_id=other_organization.id,
                provider="jira",
                status="succeeded",
                attempt_count=1,
                started_at=now + timedelta(minutes=1),
                finished_at=now + timedelta(minutes=1),
                records_synchronized=99,
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/ingestion-runs?limit=1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["provider"] == "jira"
    assert payload[0]["status"] == "failed"
    assert payload[0]["attemptCount"] == 3
    assert payload[0]["recordsSynchronized"] == 0
    assert payload[0]["errorMessage"] == "Jira request failed with status 503."


@pytest.mark.anyio
async def test_ingestion_runs_returns_error_when_default_organization_is_missing(
    app: FastAPI,
    db_session: Session,
) -> None:
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/ingestion-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Ingestion run history is unavailable."}
