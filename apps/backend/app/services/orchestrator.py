from __future__ import annotations

import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict

from app.common.logging import logger
from app.common.settings import settings
from app.persistence.models import Execution, Plan, Project
from app.persistence.repositories import append_execution_log
from app.services.policy import ensure_execution_allowed
from app.services.deployers import get_deployer, DeploymentResult


def _strip_wrapping_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and ((v[0] == v[-1]) and v[0] in {'"', "'"}):
        return v[1:-1].strip()
    return v


class Orchestrator:
    def __init__(self) -> None:
        self._log = logger.bind(component="orchestrator")

    def run(self, *, project: Project, plan: Plan, execution: Execution, session) -> None:
        """Execute a plan.

        MVP behavior is DRY-RUN by default: it logs intended actions rather than running them.
        Uses configured deploy provider (local, vercel, render) for actual deployments.
        """

        environments = json.loads(plan.environments_json)
        post_steps = json.loads(plan.post_steps_json)

        append_execution_log(session, execution, f"DRY_RUN={settings.dry_run}")
        append_execution_log(session, execution, f"DEPLOY_PROVIDER={settings.deploy_provider}")
        append_execution_log(session, execution, f"Action={plan.action} Version={plan.version} Env={environments}")
        append_execution_log(session, execution, f"PostSteps={post_steps}")

        if settings.dry_run:
            append_execution_log(
                session,
                execution,
                f"[DRY RUN] Would deploy via {settings.deploy_provider}: git checkout, build, deploy",
            )
            return

        # Use the configured deployment provider
        deploy_provider = settings.deploy_provider.lower()
        
        if deploy_provider in ("vercel", "render"):
            self._deploy_to_cloud(project, plan, execution, session, environments)
        else:
            # Local deployment (original behavior)
            self._deploy_local(project, plan, execution, session)

    def _deploy_to_cloud(
        self, project: Project, plan: Plan, execution: Execution, session, environments: list[str]
    ) -> None:
        """Deploy to cloud provider (Vercel or Render)."""
        deployer = get_deployer(settings.deploy_provider)
        
        # Validate configuration
        is_valid, error = deployer.validate_config()
        if not is_valid:
            append_execution_log(session, execution, f"ERROR: {error}")
            raise ValueError(error)
        
        append_execution_log(session, execution, f"Deploying to {deployer.name}...")
        
        # Deploy for each environment
        for env in environments:
            append_execution_log(session, execution, f"Deploying to {env}...")
            
            result = deployer.deploy(
                project_name=project.name,
                repo_path=project.repo_path,
                repo_url=project.repo_url,
                environment=env,
                version=plan.version,
            )
            
            # Log the deployment result
            if result.logs:
                for log_line in result.logs:
                    append_execution_log(session, execution, log_line)
            
            if result.deployment_url:
                append_execution_log(session, execution, f"Deployment URL: {result.deployment_url}")
            
            if not result.success:
                raise RuntimeError(f"Deployment failed: {result.message}")
            
            append_execution_log(session, execution, f"✓ {env} deployment: {result.message}")

    def _deploy_local(self, project: Project, plan: Plan, execution: Execution, session) -> None:
        """Original local deployment behavior."""
        ensure_execution_allowed()

        repo_path = _strip_wrapping_quotes(project.repo_path or "")
        if not repo_path:
            raise ValueError("Project repo_path is required for execution")

        repo_dir = Path(repo_path)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Repo path does not exist: {repo_dir}")

        env_file = repo_dir / ".env.production"
        env_vars = self._load_env_file(env_file)
        env = os.environ.copy()
        env.update(env_vars)
        env.setdefault("NODE_ENV", "production")

        npm_cmd = self._resolve_npm_command(env)
        commands = [
            npm_cmd + ["install"],
            npm_cmd + ["run", "build"],
        ]

        for cmd in commands:
            self._run_command(cmd, repo_dir, env, session, execution)

    def _load_env_file(self, path: Path) -> Dict[str, str]:
        data: Dict[str, str] = {}
        if not path.exists():
            self._log.warning("env_file_missing", path=str(path))
            return data

        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
        return data

    def _run_command(
        self,
        command: list[str],
        cwd: Path,
        env: Dict[str, str],
        session,
        execution: Execution,
    ) -> None:
        printable = " ".join(command)
        append_execution_log(session, execution, f"$ {printable}")

        process = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.stdout:
            append_execution_log(session, execution, process.stdout.strip())
        if process.stderr:
            append_execution_log(session, execution, process.stderr.strip())

        if process.returncode != 0:
            raise RuntimeError(f"Command '{printable}' failed with exit code {process.returncode}")

    def _resolve_npm_command(self, env: Dict[str, str]) -> list[str]:
        """Resolve a command that can run npm reliably on Windows.

        On Windows, npm is typically `npm.cmd` and must be launched via cmd.exe.
        Workers may not inherit the same PATH as interactive shells, so we also
        probe common installation locations.
        """

        def exists(path: str | None) -> str | None:
            if not path:
                return None
            return path if Path(path).exists() else None

        # Prefer PATH-based resolution first
        npm_path = exists(shutil.which("npm.cmd", path=env.get("PATH"))) or exists(
            shutil.which("npm", path=env.get("PATH"))
        )

        # Probe common Windows locations
        if npm_path is None:
            program_files = env.get("ProgramFiles") or os.getenv("ProgramFiles")
            appdata = env.get("APPDATA") or os.getenv("APPDATA")
            candidates: list[Path] = []
            if program_files:
                candidates.append(Path(program_files) / "nodejs" / "npm.cmd")
            if appdata:
                candidates.append(Path(appdata) / "npm.cmd")
            npm_path = next((str(p) for p in candidates if p.exists()), None)

        if npm_path is None:
            raise FileNotFoundError(
                "npm was not found. Install Node.js (which includes npm) and ensure it is on PATH for the worker process."
            )

        # Always run npm via cmd.exe for .cmd compatibility.
        # Use an absolute cmd.exe path to avoid PATH issues when the worker is launched via WSL interop.
        system_root = env.get("SystemRoot") or os.getenv("SystemRoot") or "C:\\Windows"
        cmd_exe = str(Path(system_root) / "System32" / "cmd.exe")
        if not Path(cmd_exe).exists():
            cmd_exe = "cmd.exe"
        return [cmd_exe, "/c", npm_path]
