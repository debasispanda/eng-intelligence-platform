import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", database_url=None)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
