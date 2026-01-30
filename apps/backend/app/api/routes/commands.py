from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.persistence.db import session_scope
from app.persistence.repositories import create_plan, get_project
from app.services.command_interpreter import interpret_command
from app.services.rag_advisor import advise_plan


router = APIRouter()


class CommandParseRequest(BaseModel):
    project_id: int
    text: str = Field(min_length=1, max_length=5000)


class PlanPreviewResponse(BaseModel):
    plan_id: int
    action: str
    version: str | None
    environments: list[str]
    post_steps: list[str]
    warnings: list[str]
    status: str


@router.post("/parse", response_model=PlanPreviewResponse)
def parse_command(payload: CommandParseRequest) -> PlanPreviewResponse:
    with session_scope() as session:
        project = get_project(session, payload.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        parsed = interpret_command(payload.text)
        warnings = advise_plan(
            action=parsed["action"],
            environments=parsed["environments"],
            post_steps=parsed["post_steps"],
        )

        plan = create_plan(
            session,
            project_id=project.id or 0,
            raw_command=payload.text,
            action=parsed["action"],
            version=parsed.get("version"),
            environments=parsed["environments"],
            post_steps=parsed["post_steps"],
            warnings=warnings,
        )

        return PlanPreviewResponse(
            plan_id=plan.id or 0,
            action=plan.action,
            version=plan.version,
            environments=json.loads(plan.environments_json),
            post_steps=json.loads(plan.post_steps_json),
            warnings=json.loads(plan.warnings_json),
            status=plan.status,
        )
