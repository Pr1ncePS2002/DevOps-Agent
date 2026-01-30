from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.persistence.db import session_scope
from app.persistence.repositories import (
    create_execution,
    get_execution,
    get_plan,
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

    queue = get_queue()
    job = queue.enqueue("app.queue.tasks.execute_plan", execution.id)

    return ApproveResponse(execution_id=execution.id or 0, rq_job_id=job.id)


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
