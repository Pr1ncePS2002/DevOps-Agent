from __future__ import annotations

from rq import Queue

from app.common.settings import settings
from app.queue.redis_conn import get_redis


def get_queue() -> Queue:
    return Queue(name=settings.rq_queue_name, connection=get_redis())
