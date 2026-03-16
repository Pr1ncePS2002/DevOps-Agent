from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.persistence.db import session_scope
from app.persistence.repositories import (
    append_execution_log,
    create_execution,
    get_execution,
    get_plan,
    set_execution_status,
    update_plan_status,
)
from app.queue.queue import get_queue


router = APIRouter()


class ApproveResponse(BaseModel):
    execution_id: int
    rq_job_id: str


class ExecutionResponse(BaseModel):
    id: int
    plan_id: int
    status: str
    logs: str


@router.post("/approve/{plan_id}", response_model=ApproveResponse)
def approve_plan(plan_id: int) -> ApproveResponse:
    with session_scope() as session:
        plan = get_plan(session, plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.status != "pending_approval":
            raise HTTPException(status_code=409, detail=f"Plan status is {plan.status}")

        update_plan_status(session, plan, "approved")
        execution = create_execution(session, plan_id)

        try:
            queue = get_queue()
            job = queue.enqueue("app.queue.tasks.execute_plan", execution.id)
        except Exception as exc:
            set_execution_status(session, execution, "failed")
            append_execution_log(session, execution, f"ERROR: Failed to enqueue job: {exc}")
            raise HTTPException(status_code=503, detail="Queue unavailable; execution marked failed.") from exc

    return ApproveResponse(execution_id=execution.id or 0, rq_job_id=job.id)


@router.post("/{execution_id}/rollback")
def rollback_execution(execution_id: int) -> dict:
    """Manually trigger rollback for a failed deployment."""
    from app.persistence.repositories import get_plan, get_project, get_latest_deployment, update_deployment, update_project
    from app.adapters.docker_adapter import remove_container_safe, run_container
    from app.services.env_storage import get_env_for_docker
    from pathlib import Path

    with session_scope() as session:
        execution = get_execution(session, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        plan = get_plan(session, execution.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        project = get_project(session, plan.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        tag = project.last_known_good_tag
        if not tag:
            raise HTTPException(status_code=400, detail="No last-known-good tag to rollback to")

        deploy = get_latest_deployment(session, project.id or 0)
        if deploy and deploy.container_id:
            remove_container_safe(deploy.container_id)

        env_file = get_env_for_docker(project.id or 0)
        if not env_file:
            raise HTTPException(status_code=400, detail="No env file for rollback")

        # BUG FIX: derive ports from project stack instead of hardcoding
        default_port = "3000" if project.detected_stack == "node" else "8000"
        ports = {f"{default_port}/tcp": default_port}

        ok, result = run_container(
            tag,
            name=f"devops-rollback-{project.id}"[:63],
            env_file=Path(env_file),
            ports=ports,
        )
        if not ok:
            raise HTTPException(status_code=500, detail=f"Rollback failed: {result}")

        if deploy:
            update_deployment(session, deploy, container_id=result, status="rolled_back")
        set_execution_status(session, execution, "rolled_back")
        append_execution_log(session, execution, f"Manual rollback to {tag}")

    return {"status": "ok", "message": f"Rolled back to {tag}"}


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution_endpoint(execution_id: int) -> ExecutionResponse:
    with session_scope() as session:
        execution = get_execution(session, execution_id)
        if execution is None:
            raise HTTPException(status_code=404, detail="Execution not found")

        return ExecutionResponse(
            id=execution.id or 0,
            plan_id=execution.plan_id,
            status=execution.status,
            logs=execution.logs or "",
        )
