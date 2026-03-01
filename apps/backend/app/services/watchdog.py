"""Watchdog — periodically check deployments, trigger rollback on failure."""
from __future__ import annotations

from app.adapters.docker_adapter import container_health_check, remove_container_safe
from app.common.logging import logger
from app.persistence.db import session_scope
from app.persistence.repositories import (
    append_execution_log,
    get_latest_deployment,
    get_project,
    set_execution_status,
    update_deployment,
    update_plan_status,
    update_project,
)
from app.persistence.models import Execution


def _rollback_to_last_known_good(session, project, deployment) -> bool:
    """Redeploy last-known-good image. Returns True if rollback succeeded."""
    tag = project.last_known_good_tag
    if not tag:
        return False
    # Create a minimal plan for rollback
    # We need to run container with the old image - simplified inline
    from app.adapters.docker_adapter import run_container
    from app.services.env_storage import get_env_for_docker
    from pathlib import Path

    env_file = get_env_for_docker(project.id or 0)
    if not env_file:
        return False
    ok, result = run_container(
        tag,
        name=f"devops-rollback-{project.id}",
        env_file=Path(env_file),
        ports={"3000/tcp": "3000", "8000/tcp": "8000"},
    )
    if ok and result:
        # Update deployment record
        update_deployment(session, deployment, container_id=result, status="rolled_back")
        return True
    return False


def evaluate_deployments() -> None:
    """Check all running deployments. On failure: stop container, attempt rollback."""
    log = logger.bind(component="watchdog")
    with session_scope() as session:
        # Get deployments with status running - we'd need a query for that
        # For MVP: iterate projects and check latest deployment
        from app.persistence.repositories import list_projects
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

            # Attempt rollback
            if project.last_known_good_tag and project.last_known_good_tag != deploy.image_tag:
                if _rollback_to_last_known_good(session, project, deploy):
                    log.info("rollback_succeeded", project_id=project.id)
                    # Update plan/execution if we have them
                    if deploy.execution_id:
                        exec_obj = session.get(Execution, deploy.execution_id)
                        if exec_obj:
                            append_execution_log(session, exec_obj, "Watchdog: Rolled back to last-known-good")
                            set_execution_status(session, exec_obj, "rolled_back")
                else:
                    log.error("rollback_failed", project_id=project.id)
