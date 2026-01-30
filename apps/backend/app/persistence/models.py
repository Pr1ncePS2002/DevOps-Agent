from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    repo_path: Optional[str] = None
    repo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)


class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    raw_command: str
    action: str
    version: Optional[str] = None
    environments_json: str
    post_steps_json: str
    warnings_json: str = "[]"
    status: str = "pending_approval"  # pending_approval|approved|running|failed|rolled_back|succeeded
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Execution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(index=True)
    status: str = "queued"  # queued|running|failed|succeeded|rolled_back
    logs: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_utc_now)
