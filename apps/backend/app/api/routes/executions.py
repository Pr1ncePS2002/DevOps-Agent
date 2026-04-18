from __future__ import annotations

import threading

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio

from app.persistence.db import session_scope
from app.persistence.repositories import (
    append_execution_log,
    create_execution,
    get_execution,
    get_plan,
    set_execution_status,
    update_plan_status,
)


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
        execution_id = execution.id or 0

    # Run the orchestrator in a background thread so logs stream immediately
    # without requiring a separate RQ worker process.
    from app.queue.tasks import execute_plan
    thread = threading.Thread(target=execute_plan, args=(execution_id,), daemon=True)
    thread.start()

    return ApproveResponse(execution_id=execution_id, rq_job_id=f"inline-{execution_id}")


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


class SummaryResponse(BaseModel):
    summary: str
    key_events: list[str]
    root_cause: str | None
    recommendations: list[str]
    severity: str  # info | warning | critical


@router.get("/{execution_id}/summary", response_model=SummaryResponse)
async def get_execution_summary(execution_id: int) -> SummaryResponse:
    """Return an AI-generated deployment summary / post-mortem."""
    from app.services.summary_generator import generate_deployment_summary_safe

    with session_scope() as session:
        execution = get_execution(session, execution_id)
        if execution is None:
            raise HTTPException(status_code=404, detail="Execution not found")

        if execution.status not in ("succeeded", "failed", "rolled_back"):
            raise HTTPException(status_code=409, detail="Execution not yet finished")

        result = await generate_deployment_summary_safe(execution_id, session)
        if result is None:
            return SummaryResponse(
                summary="AI summary generation failed. Check logs for details.",
                key_events=[],
                root_cause=None,
                recommendations=["Review execution logs manually"],
                severity="warning",
            )

        return SummaryResponse(**result)


@router.websocket("/{execution_id}/logs/stream")
async def stream_execution_logs(websocket: WebSocket, execution_id: int):
    """Stream live execution logs straight to the frontend without polling."""
    await websocket.accept()
    last_log_length = 0
    try:
        while True:
            # Must run sync DB lookup in thread (or via helper), but SQLModel allows
            # simple reads in async def if we're careful. Doing it threadpool is safer.
            from fastapi.concurrency import run_in_threadpool
            
            def _get_ex() -> dict | None:
                with session_scope() as session:
                    ex = get_execution(session, execution_id)
                    if not ex:
                        return None
                    return {"status": ex.status, "logs": ex.logs or ""}
            
            ex_data = await run_in_threadpool(_get_ex)
            
            if not ex_data:
                await websocket.send_text("ERROR: Execution not found")
                break
                
            current_logs = ex_data["logs"]
            if len(current_logs) > last_log_length:
                new_logs = current_logs[last_log_length:]
                await websocket.send_text(new_logs)
                last_log_length = len(current_logs)
                
            if ex_data["status"] in ("succeeded", "failed", "rolled_back"):
                # One final read happens above, so we can break safely
                break
                
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        # Client gracefully closed the connection
        pass
    except Exception as e:
        import logging
        logging.error(f"WebSocket error in log streaming: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
