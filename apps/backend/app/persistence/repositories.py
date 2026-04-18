from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.persistence.models import ChatMessage, ChatSession, Deployment, Execution, Plan, Project


def create_project(
    session: Session,
    name: str,
    repo_path: str | None = None,
    repo_url: str | None = None,
    *,
    description: str = "",
    source_type: str = "local",
    branch: str | None = None,
    workspace_path: str | None = None,
    detected_stack: str | None = None,
    dockerfile_path: str | None = None,
    has_env_file: bool = False,
    deployment_platform: str = "docker",
    deployment_config_json: str = "{}",
    env_config_json: str = "{}",
) -> Project:
    project = Project(
        name=name,
        description=description,
        source_type=source_type,
        repo_path=repo_path,
        repo_url=repo_url,
        branch=branch,
        workspace_path=workspace_path,
        detected_stack=detected_stack,
        dockerfile_path=dockerfile_path,
        has_env_file=has_env_file,
        deployment_platform=deployment_platform,
        deployment_config_json=deployment_config_json,
        env_config_json=env_config_json,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


_VALID_EXECUTION_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"running", "failed"},
    "running": {"succeeded", "failed", "rolled_back"},
    "succeeded": {"rolled_back"},   # manual rollback after successful deploy
    "failed": {"rolled_back"},      # manual rollback after failed deploy
    "rolled_back": set(),
}

_VALID_PLAN_TRANSITIONS: dict[str, set[str]] = {
    "pending_approval": {"approved", "cancelled"},
    "approved": {"running", "cancelled"},
    "running": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


def update_project(session: Session, project: Project, **kwargs) -> Project:
    for key, value in kwargs.items():
        if value is not None:
            setattr(project, key, value)
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
        status="pending_approval",
        detected_stack=detected_stack,
        dockerfile_path=dockerfile_path,
        image_tag=image_tag,
        ports_json=json.dumps(ports or []),
        env_injected=env_injected,
        updated_at=datetime.now(timezone.utc),
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_plan(session: Session, plan_id: int) -> Plan | None:
    return session.get(Plan, plan_id)


def update_plan_status(session: Session, plan: Plan, status: str) -> Plan:
    allowed = _VALID_PLAN_TRANSITIONS.get(plan.status, set())
    if status not in allowed:
        raise ValueError(
            f"Invalid plan transition: {plan.status!r} → {status!r}. "
            f"Allowed: {sorted(allowed) or 'none'}"
        )
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
    allowed = _VALID_EXECUTION_TRANSITIONS.get(execution.status, set())
    if status not in allowed:
        raise ValueError(
            f"Invalid execution transition: {execution.status!r} → {status!r}. "
            f"Allowed: {sorted(allowed) or 'none'}"
        )
    execution.status = status
    if status == "running" and execution.started_at is None:
        execution.started_at = datetime.now(timezone.utc)
    if status in {"failed", "succeeded", "rolled_back"}:
        execution.finished_at = datetime.now(timezone.utc)
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution


def create_deployment(
    session: Session,
    *,
    project_id: int,
    execution_id: int | None = None,
    container_id: str | None = None,
    image_tag: str | None = None,
    status: str = "running",
) -> Deployment:
    deployment = Deployment(
        project_id=project_id,
        execution_id=execution_id,
        container_id=container_id,
        image_tag=image_tag,
        status=status,
    )
    session.add(deployment)
    session.commit()
    session.refresh(deployment)
    return deployment


def get_latest_deployment(session: Session, project_id: int) -> Deployment | None:
    return session.exec(
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
    ).first()


def update_deployment(session: Session, deployment: Deployment, **kwargs) -> Deployment:
    for key, value in kwargs.items():
        setattr(deployment, key, value)
    session.add(deployment)
    session.commit()
    session.refresh(deployment)
    return deployment


def list_executions_for_project(session: Session, project_id: int, limit: int = 10) -> list[Execution]:
    return list(
        session.exec(
            select(Execution)
            .join(Plan, Execution.plan_id == Plan.id)
            .where(Plan.project_id == project_id)
            .order_by(Execution.created_at.desc())
            .limit(limit)
        ).all()
    )


# ── Chat / Conversation ───────────────────────────────────────────────────────


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_chat_session(session: Session, project_id: int) -> ChatSession:
    chat_session = ChatSession(
        project_id=project_id,
        created_at=_utc_iso(),
        last_message_at=_utc_iso(),
        status="active",
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


def get_chat_session(session: Session, session_id: int) -> ChatSession | None:
    return session.get(ChatSession, session_id)


def list_chat_sessions(session: Session, project_id: int) -> list[ChatSession]:
    return list(
        session.exec(
            select(ChatSession)
            .where(ChatSession.project_id == project_id)
            .order_by(ChatSession.created_at.desc())
        ).all()
    )


def add_chat_message(
    session: Session,
    *,
    session_id: int,
    role: str,
    content: str,
    message_type: str = "text",
    metadata: dict | None = None,
) -> ChatMessage:
    now = _utc_iso()
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_type=message_type,
        metadata_json=json.dumps(metadata or {}),
        created_at=now,
    )
    session.add(msg)

    # Update session last_message_at
    chat_session = session.get(ChatSession, session_id)
    if chat_session:
        chat_session.last_message_at = now
        session.add(chat_session)

    session.commit()
    session.refresh(msg)
    return msg


def get_chat_history(session: Session, session_id: int, limit: int = 50) -> list[ChatMessage]:
    return list(
        session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        ).all()
    )
