from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_type: str = "local"  # local | github
    repo_path: Optional[str] = None  # local path or workspace subdir after clone
    repo_url: Optional[str] = None  # for github
    workspace_path: Optional[str] = None  # resolved path (local or cloned)
    detected_stack: Optional[str] = None  # node | python | docker
    dockerfile_path: Optional[str] = None  # path to Dockerfile
    has_env_file: bool = False
    last_known_good_tag: Optional[str] = None  # for rollback
    created_at: datetime = Field(default_factory=_utc_now)


class Deployment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    execution_id: Optional[int] = None
    container_id: Optional[str] = None
    image_tag: Optional[str] = None
    status: str = "pending"  # pending|running|succeeded|failed|rolled_back
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    raw_command: str
    action: str
    version: Optional[str] = None
    environments_json: str
    post_steps_json: str
    warnings_json: str = "[]"
    detected_stack: Optional[str] = None
    dockerfile_path: Optional[str] = None
    image_tag: Optional[str] = None
    ports_json: str = "[]"  # e.g. ["3000:3000"]
    env_injected: bool = False
    status: str = "pending_approval"  # pending_approval|approved|running|failed|rolled_back|succeeded
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Execution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(index=True)
    status: str = "queued"  # queued|running|failed|succeeded|rolled_back
    logs: str = ""
    correlation_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_utc_now)
