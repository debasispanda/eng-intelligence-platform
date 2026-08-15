from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import app.models
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", database_url=None)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def db_session() -> Session:
    database_url = get_settings().database_url
    if database_url is None:
        pytest.skip("DATABASE_URL is required for persistence tests.")

    schema = f"test_{uuid4().hex}"
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection = connection.execution_options(schema_translate_map={None: schema})
        Base.metadata.create_all(connection)

    session = Session(engine.execution_options(schema_translate_map={None: schema}))

    try:
        yield session
    finally:
        session.close()
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()
