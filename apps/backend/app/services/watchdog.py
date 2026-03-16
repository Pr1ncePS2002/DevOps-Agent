"""Watchdog — periodically check deployments, trigger rollback on failure."""
from __future__ import annotations

import json
from pathlib import Path

from app.adapters.docker_adapter import container_health_check, remove_container_safe, run_container
from app.common.logging import logger
from app.persistence.db import session_scope
from app.persistence.repositories import (
    append_execution_log,
    create_deployment,
    get_latest_deployment,
    get_project,
    list_projects,
    set_execution_status,
    update_deployment,
    update_plan_status,
    update_project,
)
from app.persistence.models import Execution
from app.services.env_storage import get_env_for_docker


def _resolve_ports(project, deployment) -> dict[str, str]:
    """Derive port mapping from project stack instead of hardcoding."""
    default_port = "3000" if project.detected_stack == "node" else "8000"
    return {f"{default_port}/tcp": default_port}


def _rollback_to_last_known_good(session, project, deployment) -> bool:
    """Redeploy last-known-good image. Returns True if rollback succeeded."""
    tag = project.last_known_good_tag
    if not tag:
        return False

    env_file = get_env_for_docker(project.id or 0)
    if not env_file:
        return False

    ports = _resolve_ports(project, deployment)

    ok, result = run_container(
        tag,
        name=f"devops-rollback-{project.id}"[:63],
        env_file=Path(env_file),
        ports=ports,
    )
    if ok and result:
        # BUG FIX: create a new deployment record for the rollback container
        rollback_deploy = create_deployment(
            session,
            project_id=project.id or 0,
            execution_id=deployment.execution_id,
            container_id=result,
            image_tag=tag,
            status="running",
        )
        update_deployment(session, deployment, status="rolled_back")
        return True
    return False


def evaluate_deployments() -> None:
    """Check all running deployments. On failure: stop container, attempt rollback."""
    log = logger.bind(component="watchdog")
    with session_scope() as session:
        projects = list_projects(session)
        for project in projects:
            deploy = get_latest_deployment(session, project.id or 0)
            if not deploy or deploy.status != "running":
                continue
            cid = deploy.container_id
            if not cid:
                continue
            if container_health_check(cid):
                continue
            log.warning("deployment_unhealthy", project_id=project.id, container_id=cid[:12])
            remove_container_safe(cid)
            update_deployment(session, deploy, status="failed")

            if project.last_known_good_tag and project.last_known_good_tag != deploy.image_tag:
                if _rollback_to_last_known_good(session, project, deploy):
                    log.info("rollback_succeeded", project_id=project.id)
                    if deploy.execution_id:
                        exec_obj = session.get(Execution, deploy.execution_id)
                        if exec_obj:
                            append_execution_log(session, exec_obj, "Watchdog: Rolled back to last-known-good")
                            set_execution_status(session, exec_obj, "rolled_back")
                else:
                    log.error("rollback_failed", project_id=project.id)
