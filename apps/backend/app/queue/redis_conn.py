from __future__ import annotations

from redis import Redis

from app.common.settings import settings


def get_redis() -> Redis:
    # IMPORTANT: RQ stores job payloads as binary data (pickle by default).
    # Setting decode_responses=True forces Redis-py to decode bytes as UTF-8
    # and can crash the worker with UnicodeDecodeError when reading job hashes.
    return Redis.from_url(settings.redis_url, decode_responses=False)
