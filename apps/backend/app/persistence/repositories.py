from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.persistence.models import Deployment, Execution, Plan, Project


def create_project(
    session: Session,
    name: str,
    source_type: str = "local",
    repo_path: str | None = None,
    repo_url: str | None = None,
    workspace_path: str | None = None,
    detected_stack: str | None = None,
    dockerfile_path: str | None = None,
    has_env_file: bool = False,
    last_known_good_tag: str | None = None,
) -> Project:
    project = Project(
        name=name,
        source_type=source_type,
        repo_path=repo_path,
        repo_url=repo_url,
        workspace_path=workspace_path,
        detected_stack=detected_stack,
        dockerfile_path=dockerfile_path,
        has_env_file=has_env_file,
        last_known_good_tag=last_known_good_tag,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def update_project(
    session: Session,
    project: Project,
    *,
    workspace_path: str | None = None,
    detected_stack: str | None = None,
    dockerfile_path: str | None = None,
    has_env_file: bool | None = None,
    last_known_good_tag: str | None = None,
) -> Project:
    if workspace_path is not None:
        project.workspace_path = workspace_path
    if detected_stack is not None:
        project.detected_stack = detected_stack
    if dockerfile_path is not None:
        project.dockerfile_path = dockerfile_path
    if has_env_file is not None:
        project.has_env_file = has_env_file
    if last_known_good_tag is not None:
        project.last_known_good_tag = last_known_good_tag
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session) -> list[Project]:
    return list(session.exec(select(Project).order_by(Project.created_at.desc())).all())


def get_project(session: Session, project_id: int) -> Project | None:
    return session.get(Project, project_id)


def create_plan(
    session: Session,
    *,
    project_id: int,
    raw_command: str,
    action: str,
    version: str | None,
    environments: list[str],
    post_steps: list[str],
    warnings: list[str],
    detected_stack: str | None = None,
    dockerfile_path: str | None = None,
    image_tag: str | None = None,
    ports: list[str] | None = None,
    env_injected: bool = False,
) -> Plan:
    plan = Plan(
        project_id=project_id,
        raw_command=raw_command,
        action=action,
        version=version,
        environments_json=json.dumps(environments),
        post_steps_json=json.dumps(post_steps),
        warnings_json=json.dumps(warnings),
        detected_stack=detected_stack,
        dockerfile_path=dockerfile_path,
        image_tag=image_tag,
        ports_json=json.dumps(ports or []),
        env_injected=env_injected,
        status="pending_approval",
        updated_at=datetime.now(timezone.utc),
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_plan(session: Session, plan_id: int) -> Plan | None:
    return session.get(Plan, plan_id)


def update_plan_status(session: Session, plan: Plan, status: str) -> Plan:
    plan.status = status
    plan.updated_at = datetime.now(timezone.utc)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def create_execution(session: Session, plan_id: int) -> Execution:
    execution = Execution(plan_id=plan_id, status="queued")
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution


def get_execution(session: Session, execution_id: int) -> Execution | None:
    return session.get(Execution, execution_id)


def append_execution_log(session: Session, execution: Execution, line: str) -> Execution:
    execution.logs = (execution.logs or "") + line + "\n"
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution


def create_deployment(
    session: Session,
    project_id: int,
    execution_id: int | None = None,
    container_id: str | None = None,
    image_tag: str | None = None,
    status: str = "pending",
) -> Deployment:
    deploy = Deployment(
        project_id=project_id,
        execution_id=execution_id,
        container_id=container_id,
        image_tag=image_tag,
        status=status,
    )
    session.add(deploy)
    session.commit()
    session.refresh(deploy)
    return deploy


def get_latest_deployment(session: Session, project_id: int) -> Deployment | None:
    deployments = list(
        session.exec(
            select(Deployment)
            .where(Deployment.project_id == project_id)
            .order_by(Deployment.created_at.desc())
            .limit(1)
        ).all()
    )
    return deployments[0] if deployments else None


def update_deployment(
    session: Session,
    deployment: Deployment,
    *,
    container_id: str | None = None,
    image_tag: str | None = None,
    status: str | None = None,
) -> Deployment:
    if container_id is not None:
        deployment.container_id = container_id
    if image_tag is not None:
        deployment.image_tag = image_tag
    if status is not None:
        deployment.status = status
    deployment.updated_at = datetime.now(timezone.utc)
    session.add(deployment)
    session.commit()
    session.refresh(deployment)
    return deployment


def set_execution_status(session: Session, execution: Execution, status: str) -> Execution:
    execution.status = status
    if status == "running" and execution.started_at is None:
        execution.started_at = datetime.now(timezone.utc)
    if status in {"failed", "succeeded", "rolled_back"}:
        execution.finished_at = datetime.now(timezone.utc)
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution
