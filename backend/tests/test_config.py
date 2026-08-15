import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_use_local_frontend_origin_by_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.frontend_origin == "http://localhost:3000"
    assert settings.database_url is None
    assert settings.database_schema == "public"


def test_settings_reject_invalid_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="invalid", _env_file=None)


def test_settings_normalize_generic_postgresql_url() -> None:
    settings = Settings(
        database_url="postgresql://postgres:postgres@localhost:5432/platform",
        _env_file=None,
    )

    assert settings.database_url == "postgresql+psycopg://postgres:postgres@localhost:5432/platform"


def test_settings_normalize_psycopg2_url() -> None:
    settings = Settings(
        database_url="postgresql+psycopg2://postgres:postgres@localhost:5432/platform",
        _env_file=None,
    )

    assert settings.database_url == "postgresql+psycopg://postgres:postgres@localhost:5432/platform"


def test_settings_reject_invalid_database_schema() -> None:
    with pytest.raises(ValidationError):
        Settings(database_schema="Platform", _env_file=None)
