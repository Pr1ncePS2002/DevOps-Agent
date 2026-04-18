from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analytics, chat, commands, executions, projects, providers, deploy_status, demo


api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(commands.router, prefix="/commands", tags=["commands"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(deploy_status.router, prefix="/deploy", tags=["deploy-status"])
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
