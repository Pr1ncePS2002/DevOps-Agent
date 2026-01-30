from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.common.logging import configure_logging, logger
from app.common.settings import settings
from app.persistence.db import init_db


def create_app() -> FastAPI:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    app = FastAPI(title="AI DevOps Commander API", version="0.0.1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(api_router)

    init_db()
    logger.info("api_started", host=settings.host, port=settings.api_port)

    return app


app = create_app()
