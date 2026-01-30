from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import commands, executions, projects


api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(commands.router, prefix="/commands", tags=["commands"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
