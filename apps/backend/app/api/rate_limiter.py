"""
Simple in-memory rate limiter middleware for FastAPI.
Uses a sliding window counter per client IP.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic sliding-window rate limiter.

    Parameters
    ----------
    app : FastAPI application
    max_requests : Maximum requests per window (default: 60)
    window_seconds : Window size in seconds (default: 60)
    paths : Optional set of path prefixes to rate-limit.
            If None, all paths are rate-limited.
    """

    def __init__(
        self,
        app,
        max_requests: int = 60,
        window_seconds: int = 60,
        paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.paths = paths
        # {ip: [timestamp, ...]}
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for non-targeted paths
        if self.paths is not None:
            if not any(request.url.path.startswith(p) for p in self.paths):
                return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.window_seconds

        # Prune old hits outside the window
        hits = self._hits[client_ip]
        self._hits[client_ip] = [t for t in hits if t > window_start]
        hits = self._hits[client_ip]

        if len(hits) >= self.max_requests:
            retry_after = int(hits[0] - window_start) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        return await call_next(request)
