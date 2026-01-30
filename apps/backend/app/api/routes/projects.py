from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.persistence.db import session_scope
from app.persistence.repositories import create_project, list_projects


router = APIRouter()


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repo_path: str | None = None
    repo_url: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    repo_path: str | None
    repo_url: str | None


@router.post("", response_model=ProjectResponse)
def create_project_endpoint(payload: ProjectCreateRequest) -> ProjectResponse:
    if not payload.repo_path and not payload.repo_url:
        raise HTTPException(status_code=400, detail="Provide repo_path or repo_url")

    with session_scope() as session:
        project = create_project(session, payload.name, payload.repo_path, payload.repo_url)
        return ProjectResponse(id=project.id or 0, name=project.name, repo_path=project.repo_path, repo_url=project.repo_url)


@router.get("", response_model=list[ProjectResponse])
def list_projects_endpoint() -> list[ProjectResponse]:
    with session_scope() as session:
        projects = list_projects(session)
        return [
            ProjectResponse(id=p.id or 0, name=p.name, repo_path=p.repo_path, repo_url=p.repo_url)
            for p in projects
        ]
