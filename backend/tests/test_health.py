import httpx
import pytest
from fastapi import FastAPI
from redis.exceptions import ConnectionError as RedisConnectionError


@pytest.mark.anyio
async def test_health_check_returns_ok(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_health_check_allows_local_frontend_origin(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.anyio
async def test_redis_health_check_returns_ok_when_redis_is_available(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HealthyRedis:
        def ping(self) -> bool:
            return True

    monkeypatch.setattr("app.api.health.get_redis_connection", lambda: HealthyRedis())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health/redis")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_redis_health_check_returns_service_unavailable_when_redis_fails(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnhealthyRedis:
        def ping(self) -> bool:
            raise RedisConnectionError("Redis unavailable")

    monkeypatch.setattr("app.api.health.get_redis_connection", lambda: UnhealthyRedis())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health/redis")

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable."}
