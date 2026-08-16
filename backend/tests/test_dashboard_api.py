import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dashboard import get_dashboard_session
from app.models import Organization, User
from app.seed import DEMO_ORGANIZATION_NAME, seed_dashboard_data


def _test_client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


@pytest.mark.anyio
async def test_dashboard_overview_returns_seeded_data(
    app: FastAPI,
    db_session: Session,
) -> None:
    seed_dashboard_data(db_session)
    db_session.commit()
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["appTitle"] == "Engineering Intelligence"
    assert payload["profile"]["email"] == "riley.chen@example.com"
    assert len(payload["kpis"]) == 4
    assert payload["hotRepositories"]["mostActive"][0]["repository"] == "frontend-app"


@pytest.mark.anyio
async def test_dashboard_overview_returns_empty_sections_for_default_organization(
    app: FastAPI,
    db_session: Session,
) -> None:
    organization = Organization(name=DEMO_ORGANIZATION_NAME)
    db_session.add(organization)
    db_session.flush()
    db_session.add(
        User(
            organization_id=organization.id,
            name="Riley Chen",
            role="VP Engineering",
            email="riley.chen@example.com",
            avatar_initials="RC",
        )
    )
    db_session.commit()
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["kpis"] == []
    assert response.json()["releases"] == []


@pytest.mark.anyio
async def test_dashboard_overview_returns_documented_error_when_default_organization_is_missing(
    app: FastAPI,
    db_session: Session,
) -> None:
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Dashboard overview is unavailable."}


@pytest.mark.anyio
async def test_dashboard_overview_returns_documented_error_for_persistence_failure(
    app: FastAPI,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        db_session,
        "scalar",
        lambda _query: (_ for _ in ()).throw(SQLAlchemyError("Database unavailable")),
    )
    app.dependency_overrides[get_dashboard_session] = lambda: db_session

    try:
        async with _test_client(app) as client:
            response = await client.get("/dashboard/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Dashboard overview is unavailable."}
