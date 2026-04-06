"""Demo mode — one-click sample app that runs the full deploy pipeline."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.common.logging import logger
from app.common.settings import settings
from app.persistence.db import session_scope
from app.persistence.repositories import (
    create_plan,
    create_project,
    get_project,
    update_project,
)
from app.services.env_storage import store_env
from app.services.project_analysis import analyze_project

router = APIRouter()
log = logger.bind(component="demo")


def _demo_app_dir() -> Path:
    """Resolve demo app directory (the apps/demo-app created in Milestone 1)."""
    return settings.workspace_root.resolve() / "apps" / "demo-app"


def _cleanup_demo_containers() -> None:
    """Remove all devops-* containers and anything holding port 8080."""
    try:
        import docker
        client = docker.from_env()
        for c in client.containers.list(all=True):
            tags = c.image.tags if c.image.tags else []
            is_devops = c.name.startswith("devops-")
            is_demo_tag = any("devops-demo" in t for t in tags)
            holds_port = _container_uses_port(c, "8080")
            if is_devops or is_demo_tag or holds_port:
                c.remove(force=True)
                log.info("demo_cleanup", container=c.name)
        client.close()
    except Exception:
        pass


def _container_uses_port(container, port: str) -> bool:
    """Check if a container has a port mapping that includes the given port."""
    try:
        ports = container.attrs.get("HostConfig", {}).get("PortBindings", {}) or {}
        for bindings in ports.values():
            if bindings:
                for b in bindings:
                    if b.get("HostPort") == port:
                        return True
    except Exception:
        pass
    return False


class DemoProjectResponse(BaseModel):
    project_id: int
    name: str
    detected_stack: str
    deployment_platform: str
    has_env_file: bool
    workspace_path: str
    dockerfile_path: str | None = None
    message: str


class DemoFullResponse(BaseModel):
    project_id: int
    plan_id: int
    execution_id: int
    rq_job_id: str
    name: str
    detected_stack: str
    message: str


class DemoPresetInfo(BaseModel):
    name: str
    description: str
    source_type: str
    deployment_platform: str
    detected_stack: str


class DemoListResponse(BaseModel):
    presets: list[DemoPresetInfo]


@router.get("/presets", response_model=DemoListResponse)
def list_demo_presets() -> DemoListResponse:
    """List available demo presets."""
    demo_dir = _demo_app_dir()
    available = demo_dir.exists()
    presets = []
    if available:
        presets.append(
            DemoPresetInfo(
                name="hello-node-demo",
                description="Simple Express.js server - builds in Docker, responds on /health. Full pipeline demo.",
                source_type="local",
                deployment_platform="docker",
                detected_stack="node",
            )
        )
    return DemoListResponse(presets=presets)


@router.post("/setup", response_model=DemoProjectResponse)
def setup_demo_project() -> DemoProjectResponse:
    """
    Register the bundled demo app as a project.
    Creates the project, stores a pre-filled .env, and analyzes the stack.
    """
    demo_dir = _demo_app_dir()
    if not demo_dir.exists():
        raise HTTPException(status_code=404, detail=f"Demo app not found at {demo_dir}")

    analysis = analyze_project(demo_dir)
    detected_stack = analysis["detected_stack"]
    dockerfile_path = analysis.get("dockerfile_path")

    with session_scope() as session:
        project = create_project(
            session,
            name="hello-node-demo",
            description="AI DevOps Commander demo - Express.js hello-world deployed via Docker",
            source_type="local",
            repo_path=str(demo_dir),
            workspace_path=str(demo_dir),
            deployment_platform="docker",
        )
        project_id: int = project.id or 0
        project_name: str = project.name

        update_project(
            session,
            project,
            detected_stack=detected_stack,
            dockerfile_path=dockerfile_path,
        )

        env_path = demo_dir / ".env"
        if env_path.exists():
            store_env(project_id, env_path.read_bytes())
            update_project(session, project, has_env_file=True)

        log.info("demo_setup", project_id=project_id, workspace=str(demo_dir))

    return DemoProjectResponse(
        project_id=project_id,
        name=project_name,
        detected_stack=detected_stack,
        deployment_platform="docker",
        has_env_file=True,
        workspace_path=str(demo_dir),
        dockerfile_path=dockerfile_path,
        message="Demo project registered with pre-filled .env. Ready to deploy!",
    )


class DemoRunRequest(BaseModel):
    command: str

@router.post("/run-full", response_model=DemoFullResponse)
def run_full_demo(payload: DemoRunRequest) -> DemoFullResponse:
    """
    One-click full pipeline: register, .env, plan, approve, run execution inline.
    The frontend polls /executions/{id} to stream logs in real time.
    """
    import threading
    from app.persistence.repositories import create_execution, update_plan_status

    demo_dir = _demo_app_dir()
    if not demo_dir.exists():
        raise HTTPException(status_code=404, detail=f"Demo app not found at {demo_dir}")

    try:
        _cleanup_demo_containers()

        analysis = analyze_project(demo_dir)
        detected_stack = analysis["detected_stack"]
        dockerfile_path = analysis.get("dockerfile_path")

        with session_scope() as session:
            project = create_project(
                session,
                name="hello-node-demo",
                description="AI DevOps Commander demo - full pipeline",
                source_type="local",
                repo_path=str(demo_dir),
                workspace_path=str(demo_dir),
                deployment_platform="docker",
            )
            project_id: int = project.id or 0

            update_project(
                session,
                project,
                detected_stack=detected_stack,
                dockerfile_path=dockerfile_path,
            )

            env_path = demo_dir / ".env"
            if env_path.exists():
                store_env(project_id, env_path.read_bytes())
                update_project(session, project, has_env_file=True)

            plan = create_plan(
                session,
                project_id=project_id,
                raw_command=payload.command,
                action="deploy",
                version=None,
                environments=["production"],
                post_steps=[],
                warnings=[],
                detected_stack=detected_stack,
                dockerfile_path=dockerfile_path,
                image_tag=f"devops-demo-{project_id}:latest",
                ports=["8080:8080"],
                env_injected=True,
            )
            plan_id: int = plan.id or 0

            update_plan_status(session, plan, "approved")
            execution = create_execution(session, plan_id)
            execution_id: int = execution.id or 0

        # Run inline in background thread — no worker needed, logs stream immediately
        from app.queue.tasks import execute_plan
        thread = threading.Thread(target=execute_plan, args=(execution_id,), daemon=True)
        thread.start()
        job_id = f"inline-{execution_id}"

        log.info("demo_full_run", project_id=project_id, execution_id=execution_id, job_id=job_id)

        return DemoFullResponse(
            project_id=project_id,
            plan_id=plan_id,
            execution_id=execution_id,
            rq_job_id=job_id,
            name="hello-node-demo",
            detected_stack=detected_stack,
            message="Full pipeline started! Logs are streaming to the execution endpoint.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("demo_run_full_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
