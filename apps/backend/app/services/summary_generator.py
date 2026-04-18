"""AI-powered deployment summary and post-mortem generator."""
from __future__ import annotations

import json

import structlog
from sqlmodel import Session

from app.persistence.models import Execution, Plan, Project
from app.persistence.repositories import get_execution, get_plan, get_project
from app.services.llm import get_llm_client
from app.services.prompts.post_mortem import DEPLOYMENT_SUMMARY_PROMPT

log = structlog.get_logger().bind(component="summary_generator")

_DEFAULT_SUMMARY = {
    "summary": "No AI summary available.",
    "key_events": [],
    "root_cause": None,
    "recommendations": [],
    "severity": "info",
}


async def generate_deployment_summary(execution_id: int, db_session: Session) -> dict:
    """Generate an AI-powered summary for a completed execution."""
    execution = get_execution(db_session, execution_id)
    if not execution:
        raise ValueError(f"Execution {execution_id} not found")

    plan = get_plan(db_session, execution.plan_id)
    if not plan:
        raise ValueError(f"Plan {execution.plan_id} not found")

    project = get_project(db_session, plan.project_id)
    project_name = project.name if project else "Unknown"
    detected_stack = project.detected_stack if project else "unknown"

    duration = None
    if execution.started_at and execution.finished_at:
        duration = (execution.finished_at - execution.started_at).total_seconds()

    user_prompt = (
        f"Project: {project_name}\n"
        f"Stack: {detected_stack}\n"
        f"Action: {plan.action}\n"
        f"Status: {execution.status}\n"
        f"Duration: {f'{duration:.1f}s' if duration else 'N/A'}\n"
        f"Environments: {plan.environments_json}\n"
        f"Version: {plan.version or 'latest'}\n"
        f"\n--- EXECUTION LOGS ---\n"
        f"{execution.logs or '(no logs)'}"
    )

    client = get_llm_client()
    result = await client.complete_json(
        system_prompt=DEPLOYMENT_SUMMARY_PROMPT,
        user_prompt=user_prompt,
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_events": {"type": "array", "items": {"type": "string"}},
                "root_cause": {"type": ["string", "null"]},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
            },
            "required": ["summary", "key_events", "root_cause", "recommendations", "severity"],
        },
    )

    log.info("deployment_summary_generated", execution_id=execution_id, severity=result.get("severity"))
    return result


async def generate_deployment_summary_safe(execution_id: int, db_session: Session) -> dict | None:
    """Safe wrapper — returns None on any failure instead of raising."""
    try:
        return await generate_deployment_summary(execution_id, db_session)
    except Exception as exc:
        log.warning("summary_generation_failed", execution_id=execution_id, error=str(exc))
        return None
