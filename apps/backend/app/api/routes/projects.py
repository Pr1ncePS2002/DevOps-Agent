from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.persistence.db import session_scope
from app.persistence.repositories import (
    create_project,
    get_project,
    list_projects,
    update_project,
)
from app.services.env_storage import store_env, validate_env_format
from app.services.project_analysis import analyze_project
from app.services.project_registration import register_project


router = APIRouter()


# --- Register flow ---


class RegisterRequest(BaseModel):
    source_type: str = Field(..., pattern="^(local|github)$")
    path_or_url: str = Field(..., min_length=1, max_length=2000)


class RegisterResponse(BaseModel):
    project_id: int
    name: str
    workspace_path: str
    detected_stack: str
    dockerfile_path: str | None
    dockerfile_generated: bool


@router.post("/register", response_model=RegisterResponse)
def register_project_endpoint(payload: RegisterRequest) -> RegisterResponse:
    """Register a project from local path or GitHub URL. Validates, clones if GitHub, analyzes stack."""
    try:
        workspace_path, name = register_project(payload.source_type, payload.path_or_url)
    except (FileNotFoundError, ValueError, PermissionError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    analysis = analyze_project(workspace_path)

    with session_scope() as session:
        project = create_project(
            session,
            name=name,
            source_type=payload.source_type,
            repo_path=str(workspace_path) if payload.source_type == "local" else None,
            repo_url=payload.path_or_url if payload.source_type == "github" else None,
            workspace_path=str(workspace_path),
            detected_stack=analysis["detected_stack"],
            dockerfile_path=analysis.get("dockerfile_path"),
        )
        pid = project.id or 0

    return RegisterResponse(
        project_id=pid,
        name=name,
        workspace_path=str(workspace_path),
        detected_stack=analysis["detected_stack"],
        dockerfile_path=analysis.get("dockerfile_path"),
        dockerfile_generated=analysis.get("dockerfile_generated", False),
    )


# --- Env upload ---


@router.post("/{project_id}/env")
def upload_env_endpoint(project_id: int, file: UploadFile = File(...)) -> dict:
    """Upload .env file. Stored encrypted if ENCRYPTION_KEY set. Validates format. Never logs secrets."""
    if not file.filename or not file.filename.lower().endswith(".env"):
        raise HTTPException(status_code=400, detail="File must be .env")

    with session_scope() as session:
        project = get_project(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    content = file.file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")

    valid, err = validate_env_format(text)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    store_env(project_id, content)

    with session_scope() as session:
        proj = get_project(session, project_id)
        if proj:
            update_project(session, proj, has_env_file=True)

    return {"status": "ok", "message": "Env file stored"}


# --- Analyze (for re-analysis after Dockerfile edit) ---


class AnalyzeResponse(BaseModel):
    detected_stack: str
    dockerfile_path: str | None
    dockerfile_generated: bool
    default_port: int


@router.get("/{project_id}/analyze", response_model=AnalyzeResponse)
def analyze_project_endpoint(project_id: int) -> AnalyzeResponse:
    with session_scope() as session:
        project = get_project(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        wp = project.workspace_path or project.repo_path
        if not wp:
            raise HTTPException(status_code=400, detail="No workspace path")

    analysis = analyze_project(Path(wp))
    return AnalyzeResponse(
        detected_stack=analysis["detected_stack"],
        dockerfile_path=analysis.get("dockerfile_path"),
        dockerfile_generated=analysis.get("dockerfile_generated", False),
        default_port=analysis.get("default_port", 3000),
    )


# --- Legacy + list ---


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repo_path: str | None = None
    repo_url: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    source_type: str
    repo_path: str | None
    repo_url: str | None
    workspace_path: str | None
    detected_stack: str | None
    dockerfile_path: str | None
    has_env_file: bool
    last_known_good_tag: str | None


@router.post("", response_model=ProjectResponse)
def create_project_endpoint(payload: ProjectCreateRequest) -> ProjectResponse:
    if not payload.repo_path and not payload.repo_url:
        raise HTTPException(status_code=400, detail="Provide repo_path or repo_url")

    source_type = "github" if payload.repo_url else "local"
    path_or_url = payload.repo_url or payload.repo_path or ""

    with session_scope() as session:
        project = create_project(
            session,
            name=payload.name,
            source_type=source_type,
            repo_path=payload.repo_path,
            repo_url=payload.repo_url,
            workspace_path=payload.repo_path if payload.repo_path else None,
        )
        p = project
    return ProjectResponse(
        id=p.id or 0,
        name=p.name,
        source_type=p.source_type,
        repo_path=p.repo_path,
        repo_url=p.repo_url,
        workspace_path=p.workspace_path,
        detected_stack=p.detected_stack,
        dockerfile_path=p.dockerfile_path,
        has_env_file=p.has_env_file,
        last_known_good_tag=p.last_known_good_tag,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects_endpoint() -> list[ProjectResponse]:
    with session_scope() as session:
        projects = list_projects(session)
        return [
            ProjectResponse(
                id=p.id or 0,
                name=p.name,
                source_type=getattr(p, "source_type", "local"),
                repo_path=p.repo_path,
                repo_url=p.repo_url,
                workspace_path=getattr(p, "workspace_path", None),
                detected_stack=getattr(p, "detected_stack", None),
                dockerfile_path=getattr(p, "dockerfile_path", None),
                has_env_file=getattr(p, "has_env_file", False),
                last_known_good_tag=getattr(p, "last_known_good_tag", None),
            )
            for p in projects
        ]
