from __future__ import annotations

from app.common.logging import logger
from app.persistence.db import session_scope
from app.persistence.repositories import (
    append_execution_log,
    get_execution,
    get_plan,
    get_project,
    set_execution_status,
    update_plan_status,
)
from app.services.orchestrator import Orchestrator


def execute_plan(execution_id: int) -> None:
    log = logger.bind(task="execute_plan", execution_id=execution_id)

    with session_scope() as session:
        execution = get_execution(session, execution_id)
        if execution is None:
            log.error("execution_not_found")
            return

        plan = get_plan(session, execution.plan_id)
        if plan is None:
            set_execution_status(session, execution, "failed")
            append_execution_log(session, execution, "Plan not found")
            log.error("plan_not_found")
            return

        project = get_project(session, plan.project_id)
        if project is None:
            set_execution_status(session, execution, "failed")
            append_execution_log(session, execution, "Project not found")
            log.error("project_not_found")
            return

        set_execution_status(session, execution, "running")
        update_plan_status(session, plan, "running")

        orchestrator = Orchestrator()
        try:
            orchestrator.run(project=project, plan=plan, execution=execution, session=session)
            set_execution_status(session, execution, "succeeded")
            update_plan_status(session, plan, "succeeded")
            log.info("execution_succeeded")
        except Exception as exc:  # noqa: BLE001
            append_execution_log(session, execution, f"ERROR: {exc}")
            set_execution_status(session, execution, "failed")
            update_plan_status(session, plan, "failed")
            log.exception("execution_failed")
