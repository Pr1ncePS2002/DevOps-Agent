from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.common.logging import configure_logging, logger
from app.common.settings import settings
from app.persistence.db import init_db
from app.services.watchdog import evaluate_deployments


async def watchdog_loop() -> None:
    """Periodically check all running deployments for health."""
    while True:
        try:
            await run_in_threadpool(evaluate_deployments)
        except Exception as e:
            logger.error("watchdog_iteration_error", error=str(e))
        await asyncio.sleep(60)


def _cleanup_stale_containers() -> None:
    """Remove all devops-* containers left over from previous runs."""
    try:
        import docker
        client = docker.from_env()
        for c in client.containers.list(all=True):
            if c.name.startswith("devops-"):
                c.remove(force=True)
                logger.info("startup_cleanup", container=c.name)
        client.close()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup, teardown)."""
    await run_in_threadpool(_cleanup_stale_containers)
    task = asyncio.create_task(watchdog_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    tags_metadata = [
        {"name": "projects", "description": "Project registration and management"},
        {"name": "commands", "description": "Natural-language command parsing and plan generation"},
        {"name": "executions", "description": "Deployment execution, approval, and monitoring"},
        {"name": "chat", "description": "Conversational AI interface (multi-turn)"},
        {"name": "analytics", "description": "Deployment metrics and history aggregation"},
        {"name": "providers", "description": "Cloud provider connection (Vercel, Render)"},
        {"name": "deploy-status", "description": "Deployment status polling for cloud providers"},
        {"name": "demo", "description": "Demo setup and sample data generation"},
    ]

    app = FastAPI(
        title="AI DevOps Commander API",
        version="1.0.0",
        description=(
            "AI-powered DevOps deployment platform. Parse natural-language commands "
            "into structured deployment plans, validate with RAG-based safety checks, "
            "and execute via Docker — all with real-time streaming and AI-generated analytics."
        ),
        contact={"name": "AI DevOps Commander", "url": "https://github.com/ai-devops-commander"},
        license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        openapi_tags=tags_metadata,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    # Rate-limit registration and command endpoints (30 req/min per IP)
    from app.api.rate_limiter import RateLimitMiddleware

    app.add_middleware(
        RateLimitMiddleware,
        max_requests=30,
        window_seconds=60,
        paths={"/api/projects/register", "/api/commands/parse"},
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(api_router)

    init_db()
    logger.info("api_started", host=settings.host, port=settings.api_port)

    return app


app = create_app()
