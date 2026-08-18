from collections.abc import Callable
from typing import Any
from uuid import uuid4

from redis import Redis
from rq import Queue

from app.core.config import Settings, get_settings
from app.sync_github import synchronize as synchronize_github
from app.sync_jira import synchronize as synchronize_jira


def get_redis_connection(settings: Settings | None = None) -> Redis:
    app_settings = settings or get_settings()
    # RQ stores pickled job payloads and metadata as bytes.
    return Redis.from_url(app_settings.redis_url, decode_responses=False)


def get_ingestion_queue(settings: Settings | None = None) -> Queue:
    app_settings = settings or get_settings()
    return Queue(
        app_settings.ingestion_queue_name,
        connection=get_redis_connection(app_settings),
    )


def enqueue_github_sync(settings: Settings | None = None) -> Any:
    return enqueue_sync("github", settings)


def enqueue_jira_sync(settings: Settings | None = None) -> Any:
    return enqueue_sync("jira", settings)


def enqueue_sync(provider: str, settings: Settings | None = None) -> Any:
    app_settings = settings or get_settings()
    jobs: dict[str, Callable[[], int]] = {
        "github": synchronize_github,
        "jira": synchronize_jira,
    }
    if provider not in jobs:
        raise ValueError(f"Unsupported ingestion provider: {provider}") from None
    redis = get_redis_connection(app_settings)
    lock_key = f"{app_settings.ingestion_queue_name}:active:{provider}"
    lock_token = uuid4().hex
    if not redis.set(lock_key, lock_token, nx=True, ex=app_settings.ingestion_lock_seconds):
        return None

    try:
        return get_ingestion_queue(app_settings).enqueue(
            run_sync_job,
            provider,
            lock_token,
        )
    except Exception:
        _release_lock(redis, lock_key, lock_token)
        raise


def run_sync_job(provider: str, lock_token: str) -> int:
    settings = get_settings()
    lock_key = f"{settings.ingestion_queue_name}:active:{provider}"
    jobs: dict[str, Callable[[], int]] = {
        "github": synchronize_github,
        "jira": synchronize_jira,
    }
    try:
        return jobs[provider]()
    finally:
        _release_lock(get_redis_connection(settings), lock_key, lock_token)


def _release_lock(redis: Redis, lock_key: str, lock_token: str) -> None:
    redis.eval(
        "if redis.call('get', KEYS[1]) == ARGV[1] then "
        "return redis.call('del', KEYS[1]) else return 0 end",
        1,
        lock_key,
        lock_token,
    )
