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
from app.services.registration import (
    ProjectRegistrationService,
    RegisterProjectPayload,
    RegisterProjectResponse,
)

router = APIRouter()

# ── Unified registration (NEW) ────────────────────────────────────────────────


@router.post("/register")
def register_project_endpoint(payload: RegisterProjectPayload):
    """
    Single unified project registration endpoint.

    Accepts a structured payload with:
      - source (local path or GitHub URL + branch)
      - deployment platform (local | docker | vercel | render)
      - env key-value pairs

    Validates source×platform compatibility, resolves/clones workspace,
    analyses stack (auto-generates Dockerfile if missing), and persists the project record.
    """
    from fastapi.responses import JSONResponse

    try:
        with session_scope() as session:
            result = ProjectRegistrationService().register(
                session=session,
                payload=payload,
            )
            # Serialize with camelCase aliases so frontend gets projectId, workspacePath, etc.
            return JSONResponse(content=result.model_dump(by_alias=True))
    except (FileNotFoundError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Env upload ────────────────────────────────────────────────────────────────


@router.post("/{project_id}/env")
def upload_env_endpoint(project_id: int, file: UploadFile = File(...)) -> dict:
    """Upload .env file. Stored encrypted if ENCRYPTION_KEY set. Validates format. Never logs secrets."""
    if not file.filename or not file.filename.lower().endswith(".env"):
        raise HTTPException(status_code=400, detail="File must be .env")

    content = file.file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")

    valid, err = validate_env_format(text)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    with session_scope() as session:
        project = get_project(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        store_env(project_id, content)
        update_project(session, project, has_env_file=True)

    return {"status": "ok", "message": "Env file stored"}


# ── Re-analyze ────────────────────────────────────────────────────────────────


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


# ── Project list & full detail ────────────────────────────────────────────────


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    source_type: str
    repo_path: str | None
    repo_url: str | None
    branch: str | None
    workspace_path: str | None
    detected_stack: str | None
    dockerfile_path: str | None
    has_env_file: bool
    last_known_good_tag: str | None
    deployment_platform: str
    env_warnings: list[str] = []


@router.get("", response_model=list[ProjectResponse])
def list_projects_endpoint() -> list[ProjectResponse]:
    with session_scope() as session:
        projects = list_projects(session)
        return [
            ProjectResponse(
                id=p.id or 0,
                name=p.name,
                description=getattr(p, "description", ""),
                source_type=getattr(p, "source_type", "local"),
                repo_path=p.repo_path,
                repo_url=p.repo_url,
                branch=getattr(p, "branch", None),
                workspace_path=getattr(p, "workspace_path", None),
                detected_stack=getattr(p, "detected_stack", None),
                dockerfile_path=getattr(p, "dockerfile_path", None),
                has_env_file=getattr(p, "has_env_file", False),
                last_known_good_tag=getattr(p, "last_known_good_tag", None),
                deployment_platform=getattr(p, "deployment_platform", "docker"),
            )
            for p in projects
        ]


# ── LEGACY: kept for backward compatibility (test_command_parse.py) ───────────
# DEPRECATED: use POST /projects/register instead.


class _LegacyProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repo_path: str | None = None
    repo_url: str | None = None


@router.post("", response_model=ProjectResponse, include_in_schema=False)
def _legacy_create_project_endpoint(payload: _LegacyProjectCreateRequest) -> ProjectResponse:
    """
    DEPRECATED legacy endpoint. Use POST /projects/register.
    Kept only so existing tests and integrations don't break.
    """
    if not payload.repo_path and not payload.repo_url:
        raise HTTPException(status_code=400, detail="Provide repo_path or repo_url")

    source_type = "github" if payload.repo_url else "local"

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
        description=getattr(p, "description", ""),
        source_type=p.source_type,
        repo_path=p.repo_path,
        repo_url=p.repo_url,
        branch=getattr(p, "branch", None),
        workspace_path=p.workspace_path,
        detected_stack=p.detected_stack,
        dockerfile_path=p.dockerfile_path,
        has_env_file=p.has_env_file,
        last_known_good_tag=p.last_known_good_tag,
        deployment_platform=getattr(p, "deployment_platform", "docker"),
    )
