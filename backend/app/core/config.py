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
    default_organization_name: str = "Engineering Intelligence Demo"
    github_api_url: str = "https://api.github.com"
    github_token: str | None = None
    github_page_size: int = 100
    jira_base_url: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None
    jira_project_keys: str = ""
    redis_url: str = "redis://localhost:6379/0"
    ingestion_queue_name: str = "engineering-intelligence-ingestion"
    ingestion_schedule_seconds: int = 3600

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

    @field_validator("github_page_size")
    @classmethod
    def validate_github_page_size(cls, value: int) -> int:
        if not 1 <= value <= 100:
            raise ValueError("GITHUB_PAGE_SIZE must be between 1 and 100.")

        return value

    @field_validator("ingestion_schedule_seconds")
    @classmethod
    def validate_ingestion_schedule_seconds(cls, value: int) -> int:
        if value < 60:
            raise ValueError("INGESTION_SCHEDULE_SECONDS must be at least 60.")
        return value

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
