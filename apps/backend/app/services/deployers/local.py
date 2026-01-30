from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from app.common.logging import logger
from app.common.settings import settings
from app.services.deployers.base import BaseDeployer, DeploymentResult


class LocalDeployer(BaseDeployer):
    """Local deployment provider for running builds locally."""
    
    def __init__(self) -> None:
        self._log = logger.bind(component="local-deployer")
    
    @property
    def name(self) -> str:
        return "Local"
    
    def validate_config(self) -> tuple[bool, str]:
        if not settings.enable_local_execution:
            return False, "ENABLE_LOCAL_EXECUTION must be true for local deployments"
        return True, ""
    
    def deploy(
        self,
        *,
        project_name: str,
        repo_path: str | None = None,
        repo_url: str | None = None,
        environment: str = "production",
        version: str | None = None,
    ) -> DeploymentResult:
        """
        Run local build commands.
        """
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        if not repo_path:
            return DeploymentResult(
                success=False,
                message="repo_path is required for local deployments"
            )
        
        logs: list[str] = []
        repo_dir = Path(repo_path)
        
        if not repo_dir.exists():
            return DeploymentResult(
                success=False,
                message=f"Repository path does not exist: {repo_dir}"
            )
        
        try:
            logs.append(f"Starting local deployment for {project_name}")
            logs.append(f"Directory: {repo_dir}")
            logs.append(f"Environment: {environment}")
            
            # Load environment variables
            env_file = repo_dir / ".env.production"
            env_vars = self._load_env_file(env_file)
            env = os.environ.copy()
            env.update(env_vars)
            env.setdefault("NODE_ENV", "production")
            
            # Resolve npm command
            npm_cmd = self._resolve_npm_command(env)
            
            # Run commands
            commands = [
                npm_cmd + ["install"],
                npm_cmd + ["run", "build"],
            ]
            
            for cmd in commands:
                result = self._run_command(cmd, repo_dir, env, logs)
                if not result:
                    return DeploymentResult(
                        success=False,
                        message="Build command failed",
                        logs=logs,
                    )
            
            logs.append("Local build completed successfully!")
            
            return DeploymentResult(
                success=True,
                message="Local deployment completed",
                logs=logs,
                metadata={"environment": environment},
            )
            
        except Exception as e:
            self._log.exception("local_deploy_failed", error=str(e))
            logs.append(f"Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
    
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
        logs: list[str],
    ) -> bool:
        printable = " ".join(command)
        logs.append(f"$ {printable}")
        
        process = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if process.stdout:
            logs.append(process.stdout.strip())
        if process.stderr:
            logs.append(process.stderr.strip())
        
        if process.returncode != 0:
            logs.append(f"Command failed with exit code {process.returncode}")
            return False
        
        return True
    
    def _resolve_npm_command(self, env: Dict[str, str]) -> list[str]:
        """Resolve npm command for the current platform."""
        
        def exists(path: str | None) -> str | None:
            if not path:
                return None
            return path if Path(path).exists() else None
        
        npm_path = exists(shutil.which("npm.cmd", path=env.get("PATH"))) or exists(
            shutil.which("npm", path=env.get("PATH"))
        )
        
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
            raise FileNotFoundError("npm was not found. Install Node.js.")
        
        system_root = env.get("SystemRoot") or os.getenv("SystemRoot") or "C:\\Windows"
        cmd_exe = str(Path(system_root) / "System32" / "cmd.exe")
        if not Path(cmd_exe).exists():
            cmd_exe = "cmd.exe"
        return [cmd_exe, "/c", npm_path]
    
    def get_deployment_status(self, deployment_id: str) -> DeploymentResult:
        """Local deployments don't have persistent status."""
        return DeploymentResult(
            success=True,
            message="Local deployments complete synchronously",
            deployment_id=deployment_id,
        )
    
    def rollback(self, deployment_id: str) -> DeploymentResult:
        """Local rollback would need git operations."""
        return DeploymentResult(
            success=False,
            message="Local rollback not implemented. Use git to checkout previous version.",
        )
