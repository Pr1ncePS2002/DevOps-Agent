from __future__ import annotations

import os
import signal

from redis.exceptions import ConnectionError as RedisConnectionError

from rq import Worker
from rq.worker import SimpleWorker

from rq.timeouts import TimerDeathPenalty

from app.common.logging import configure_logging, logger
from app.common.settings import settings
from app.queue.redis_conn import get_redis


def main() -> None:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    redis_conn = get_redis()
    log = logger.bind(component="rq-worker", queue=settings.rq_queue_name)
    log.info("worker_starting")

    # Fail fast with a clear message if Redis isn't reachable.
    try:
        redis_conn.ping()
    except RedisConnectionError as exc:
        log.error(
            "redis_unreachable",
            redis_url=settings.redis_url,
            hint="Start Redis (Docker/Memurai) and re-run scripts\\run-worker.cmd",
            error=str(exc),
        )
        raise SystemExit(1) from exc

    # RQ workers fork by default, which is not available on Windows.
    # When running via Windows Python (even from WSL paths), fall back to SimpleWorker.
    worker_cls = Worker if hasattr(os, "fork") else SimpleWorker
    worker = worker_cls([settings.rq_queue_name], connection=redis_conn)

    # RQ's default job timeout mechanism uses SIGALRM which is unavailable on Windows.
    # Use a thread-based timeout implementation instead.
    if not hasattr(signal, "SIGALRM"):
        worker.death_penalty_class = TimerDeathPenalty

    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
