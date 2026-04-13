import os

import redis
from redis import Redis

_redis_client: Redis | None = None


def _build_redis_url() -> str | None:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis_url

    redis_host = os.getenv("REDIS_HOST")
    if not redis_host:
        return None

    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = os.getenv("REDIS_DB", "0")
    redis_password = os.getenv("REDIS_PASSWORD", "")

    auth = f":{redis_password}@" if redis_password else ""
    return f"redis://{auth}{redis_host}:{redis_port}/{redis_db}"


def init_redis() -> Redis | None:
    global _redis_client
    redis_url = _build_redis_url()
    if not redis_url:
        return None

    _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    _redis_client.ping()
    return _redis_client


def get_redis_client() -> Redis | None:
    return _redis_client


def close_redis() -> None:
    global _redis_client
    if _redis_client is None:
        return
    _redis_client.close()
    _redis_client = None
