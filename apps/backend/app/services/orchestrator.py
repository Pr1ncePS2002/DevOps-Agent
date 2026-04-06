"""Orchestrator — validate → git pull → docker build → docker run → health check → register."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from app.adapters.docker_adapter import (
    build_image,
    container_health_check,
    remove_container_safe,
    run_container,
)
from app.common.logging import logger
from app.common.settings import settings
from app.persistence.models import Execution, Plan, Project
from app.persistence.repositories import (
    append_execution_log,
    create_deployment,
    get_latest_deployment,
    update_deployment,
    update_plan_status,
    update_project,
)
from app.services.env_storage import get_env_for_docker
from app.services.policy import ensure_execution_allowed


def _log(session, execution: Execution, msg: str) -> None:
    append_execution_log(session, execution, msg)


class Orchestrator:
    def __init__(self) -> None:
        self._log = logger.bind(component="orchestrator")

    def run(self, *, project: Project, plan: Plan, execution: Execution, session) -> None:
        """Execute deployment plan. Deterministic steps. Uses Docker adapter (no raw shell)."""
        if settings.dry_run:
            _log(session, execution, "[DRY RUN] Would: validate → build → run → health check")
            return

        ensure_execution_allowed()

        cid = str(uuid.uuid4())[:8]
        _log(session, execution, f"[{cid}] Starting deployment pipeline")

        # BUG FIX: use per-project deployment_platform, not global settings.deploy_provider
        deploy_provider = (
            getattr(project, "deployment_platform", None)
            or settings.deploy_provider
            or "docker"
        ).lower()
        if deploy_provider in ("vercel", "render"):
            self._deploy_to_cloud(project, plan, execution, session)
            return

        try:
            self._deploy_docker(project, plan, execution, session, cid)
        except Exception as exc:
            _log(session, execution, f"ERROR: {exc}")
            raise

    def _deploy_docker(
        self, project: Project, plan: Plan, execution: Execution, session, correlation_id: str
    ) -> None:
        workspace_path = project.workspace_path or project.repo_path
        if not workspace_path:
            raise ValueError("Project has no workspace_path or repo_path")

        wp = Path(workspace_path).resolve()

        # Security: verify the resolved path is within allowed directories.
        # If ALLOWED_REPO_ROOTS is empty (demo mode) any existing path is permitted.
        if settings.allowed_repo_roots:
            allowed_roots = [
                Path(r.strip()).resolve()
                for r in settings.allowed_repo_roots.split(",")
                if r.strip()
            ]
            if not any(wp == root or root in wp.parents for root in allowed_roots):
                raise ValueError(
                    f"Invalid path: {wp} is outside allowed directories. "
                    f"Add it to ALLOWED_REPO_ROOTS or move the project to the workspace."
                )

        if not wp.exists():
            raise FileNotFoundError(f"Workspace does not exist: {wp}")

        image_tag = plan.image_tag or f"devops-cmd-{project.id}:latest"
        dockerfile_path = plan.dockerfile_path or (wp / "Dockerfile")
        if isinstance(dockerfile_path, str):
            df_path = Path(dockerfile_path)
        else:
            df_path = dockerfile_path

        if not df_path.exists():
            from app.services.project_analysis import analyze_project
            _log(session, execution, "[*] Dockerfile not found, attempting auto-generation...")
            try:
                analysis = analyze_project(wp)
                if analysis.get("dockerfile_generated") and analysis.get("dockerfile_path"):
                    df_path = Path(analysis["dockerfile_path"])
                    _log(session, execution, f"  ✓ Generated Dockerfile for stack: {analysis.get('detected_stack')}")
                else:
                    raise FileNotFoundError(f"Dockerfile not found and could not be auto-generated for: {wp}")
            except Exception as e:
                raise FileNotFoundError(f"Dockerfile not found and auto-generation failed: {e}")

        # 1. Validate
        _log(session, execution, "[1/6] Validating project state")
        if not project.has_env_file:
            raise ValueError("No .env file. Upload env before deployment.")
        _log(session, execution, "  ✓ Env file present")

        # 2. Git pull (if GitHub) - skip for now to keep deterministic
        _log(session, execution, "[2/6] Git pull (skipped for local)")

        # 3. Docker build
        _log(session, execution, f"[3/6] Docker build: {image_tag}")

        def log_cb(line: str) -> None:
            _log(session, execution, f"  {line}")

        ok, msg = build_image(
            context_path=wp,
            dockerfile_path=df_path,
            tag=image_tag,
            timeout=600,
            log_callback=log_cb,
        )
        if not ok:
            raise RuntimeError(f"Docker build failed: {msg}")
        _log(session, execution, "  ✓ Build succeeded")

        # 4. Stop old container if exists
        latest = get_latest_deployment(session, project.id or 0)
        old_cid = latest.container_id if latest and latest.status == "running" else None
        if old_cid:
            _log(session, execution, f"  Stopping previous container {old_cid[:12]}...")
            remove_container_safe(old_cid)
            if latest:
                update_deployment(session, latest, status="stopped")

        # 5. Docker run with env vars
        _log(session, execution, "[4/6] Starting container")
        env_file = get_env_for_docker(project.id or 0)
        if not env_file:
            raise ValueError("Env file not available for container")

        # Determine port — priority: Dockerfile EXPOSE > .env PORT= > stack default
        app_port = None

        # 1. Read EXPOSE from Dockerfile (most reliable source of truth)
        try:
            df_text = df_path.read_text(errors="ignore")
            for line in df_text.splitlines():
                stripped = line.strip().upper()
                if stripped.startswith("EXPOSE "):
                    val = stripped.split()[1].split("/")[0]
                    if val.isdigit():
                        app_port = val
                        break
        except Exception:
            pass

        # 2. Fallback: PORT= or APP_PORT= in the project .env file
        if not app_port and Path(env_file).exists():
            for line in Path(env_file).read_text(errors="ignore").splitlines():
                if line.startswith("PORT=") or line.startswith("APP_PORT="):
                    val = line.split("=", 1)[1].strip().strip("\"'")
                    if val.isdigit():
                        app_port = val
                    break

        # 3. Final fallback: stack default
        if not app_port:
            app_port = "8080" if project.detected_stack == "node" else "8000"

        ports_dict = {f"{app_port}/tcp": app_port}

        # Free any container already holding our target ports before starting
        try:
            import docker as _docker
            _client = _docker.from_env()
            host_ports = set(ports_dict.values())
            for _c in _client.containers.list(all=True):
                if _c.name.startswith("devops-"):
                    _c.remove(force=True)
                    continue
                _bindings = (_c.attrs.get("HostConfig") or {}).get("PortBindings") or {}
                for _binds in _bindings.values():
                    for _b in (_binds or []):
                        if _b.get("HostPort") in host_ports:
                            _c.remove(force=True)
                            break
            _client.close()
        except Exception:
            pass

        ok, result = run_container(
            image_tag,
            name=f"devops-{project.id}-{correlation_id}"[:63],
            env_file=Path(env_file),
            ports=ports_dict,
        )
        if not ok or not result:
            raise RuntimeError(f"Docker run failed: {result}")
        container_id = result
        _log(session, execution, f"  ✓ Container started: {container_id[:12]}")

        # 6. Health check (with retries handled inside adapter)
        _log(session, execution, "[5/6] Health check")
        if not container_health_check(container_id, retries=5, interval=2.0):
            remove_container_safe(container_id)
            raise RuntimeError("Container failed health check (not running)")
        _log(session, execution, "  ✓ Container is running")

        # 7. Register deployment + store last-known-good
        _log(session, execution, "[6/6] Registering deployment")
        deploy = create_deployment(
            session,
            project_id=project.id or 0,
            execution_id=execution.id,
            container_id=container_id,
            image_tag=image_tag,
            status="running",
        )
        update_project(session, project, last_known_good_tag=image_tag)
        _log(session, execution, f"  ✓ Deployment registered. Last-known-good: {image_tag}")

        try:
            primary_port = list(ports_dict.values())[0] if ports_dict else "unknown"
            _log(session, execution, "")
            _log(session, execution, f"🚀 **App is live at: http://localhost:{primary_port}**")
        except Exception:
            pass

    def _deploy_to_cloud(
        self, project: Project, plan: Plan, execution: Execution, session
    ) -> None:
        """Cloud providers (Vercel, Render)."""
        from app.services.deployers import get_deployer

        # BUG FIX: use project-level platform, not global settings.deploy_provider
        provider = (
            getattr(project, "deployment_platform", None)
            or settings.deploy_provider
        )
        deployer = get_deployer(provider)
        is_valid, error = deployer.validate_config()
        if not is_valid:
            _log(session, execution, f"ERROR: {error}")
            raise ValueError(error)

        environments = json.loads(plan.environments_json)
        # BUG FIX: if no environments specified, default to ["production"]
        if not environments:
            environments = ["production"]

        for env in environments:
            _log(session, execution, f"Deploying to {env}...")
            result = deployer.deploy(
                project_name=project.name,
                repo_path=project.repo_path,
                repo_url=project.repo_url,
                environment=env,
                version=plan.version,
            )
            if result.logs:
                for line in result.logs:
                    _log(session, execution, line)
            if not result.success:
                raise RuntimeError(f"Deployment failed: {result.message}")
