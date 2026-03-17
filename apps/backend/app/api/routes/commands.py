from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.persistence.db import session_scope
from app.persistence.repositories import create_plan, get_project
from app.services.command_interpreter import interpret_command, build_deployment_plan
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
    project_id: int
    repo_path: str | None
    detected_stack: str | None
    dockerfile_path: str | None
    image_tag: str | None
    ports: list[str]
    env_injected: bool


@router.post("/parse", response_model=PlanPreviewResponse)
def parse_command(payload: CommandParseRequest) -> PlanPreviewResponse:
    with session_scope() as session:
        project = get_project(session, payload.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        parsed = interpret_command(payload.text)
        rag_warnings = advise_plan(
            action=parsed["action"],
            environments=parsed["environments"],
            post_steps=parsed["post_steps"],
        )

        repo_path = project.workspace_path or project.repo_path or ""
        default_port = 3000 if (project.detected_stack or "node") == "node" else 8000
        dp = build_deployment_plan(
            project_id=project.id or 0,
            repo_path=repo_path,
            detected_stack=project.detected_stack or "unknown",
            dockerfile_path=project.dockerfile_path,
            has_env_file=project.has_env_file,
            default_port=default_port,
            parsed=parsed,
        )
        warnings = dp["warnings"] + rag_warnings

        plan = create_plan(
            session,
            project_id=project.id or 0,
            raw_command=payload.text,
            action=parsed["action"],
            version=parsed.get("version"),
            environments=parsed["environments"],
            post_steps=parsed["post_steps"],
            warnings=warnings,
            detected_stack=dp["detected_stack"],
            dockerfile_path=dp["dockerfile_path"],
            image_tag=dp["image_tag"],
            ports=dp["ports"],
            env_injected=dp["env_injected"],
        )

        return PlanPreviewResponse(
            plan_id=plan.id or 0,
            action=plan.action,
            version=plan.version,
            environments=json.loads(plan.environments_json),
            post_steps=json.loads(plan.post_steps_json),
            warnings=json.loads(plan.warnings_json),
            status=plan.status,
            project_id=dp["project_id"],
            repo_path=dp["repo_path"],
            detected_stack=dp["detected_stack"],
            dockerfile_path=dp["dockerfile_path"],
            image_tag=dp["image_tag"],
            ports=json.loads(plan.ports_json),
            env_injected=dp["env_injected"],
        )
