from fastapi import APIRouter, HTTPException
from redis.exceptions import RedisError

from app.queue import get_redis_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/redis")
def redis_health_check() -> dict[str, str]:
    try:
        get_redis_connection().ping()
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis is unavailable.") from None
    return {"status": "ok"}
