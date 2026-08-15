import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Engineering Intelligence API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    frontend_origin: str = "http://localhost:3000"
    database_url: str | None = None
    database_schema: str = "public"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str | None) -> str | None:
        if value is None:
            return None

        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql+psycopg2://"):
            return value.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

        return value

    @field_validator("database_schema")
    @classmethod
    def validate_database_schema(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", value):
            raise ValueError("DATABASE_SCHEMA must be a lowercase PostgreSQL identifier.")

        return value

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
