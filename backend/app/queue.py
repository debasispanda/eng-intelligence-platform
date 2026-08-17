from collections.abc import Callable
from typing import Any

from redis import Redis
from rq import Queue

from app.core.config import Settings, get_settings
from app.sync_github import synchronize as synchronize_github
from app.sync_jira import synchronize as synchronize_jira


def get_redis_connection(settings: Settings | None = None) -> Redis:
    app_settings = settings or get_settings()
    return Redis.from_url(app_settings.redis_url, decode_responses=True)


def get_ingestion_queue(settings: Settings | None = None) -> Queue:
    app_settings = settings or get_settings()
    return Queue(
        app_settings.ingestion_queue_name,
        connection=get_redis_connection(app_settings),
    )


def enqueue_github_sync(settings: Settings | None = None) -> Any:
    return get_ingestion_queue(settings).enqueue(synchronize_github)


def enqueue_jira_sync(settings: Settings | None = None) -> Any:
    return get_ingestion_queue(settings).enqueue(synchronize_jira)


def enqueue_sync(provider: str, settings: Settings | None = None) -> Any:
    jobs: dict[str, Callable[[], int]] = {
        "github": synchronize_github,
        "jira": synchronize_jira,
    }
    try:
        job = jobs[provider]
    except KeyError:
        raise ValueError(f"Unsupported ingestion provider: {provider}") from None
    return get_ingestion_queue(settings).enqueue(job)
