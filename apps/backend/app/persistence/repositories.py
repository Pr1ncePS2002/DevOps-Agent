from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.persistence.models import Execution, Plan, Project


def create_project(session: Session, name: str, repo_path: str | None, repo_url: str | None) -> Project:
    project = Project(name=name, repo_path=repo_path, repo_url=repo_url)
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
) -> Plan:
    plan = Plan(
        project_id=project_id,
        raw_command=raw_command,
        action=action,
        version=version,
        environments_json=json.dumps(environments),
        post_steps_json=json.dumps(post_steps),
        warnings_json=json.dumps(warnings),
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
