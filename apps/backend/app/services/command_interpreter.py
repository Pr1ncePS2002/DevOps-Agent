"""Command interpreter — produces structured DeploymentPlan. Deterministic."""
from __future__ import annotations

import re


def interpret_command(text: str) -> dict:
    """Deterministic parser. Produces plan-like dict."""
    normalized = text.strip()
    lowered = normalized.lower()

    action = "deploy" if "deploy" in lowered else ("rollback" if "rollback" in lowered else "unknown")

    version_match = re.search(r"\bv?(\d+\.\d+(?:\.\d+)*)\b", lowered)
    version = version_match.group(1) if version_match else None

    envs: list[str] = []
    for env in ["dev", "staging", "stage", "prod", "production"]:
        if env in lowered:
            envs.append("staging" if env == "stage" else ("production" if env == "prod" else env))
    if not envs:
        envs = ["staging"]

    post_steps: list[str] = []
    if "test" in lowered:
        post_steps.append("run_tests")
    if "smoke" in lowered:
        post_steps.append("smoke_tests")

    return {
        "action": action,
        "version": version,
        "environments": envs,
        "post_steps": post_steps,
    }


def build_deployment_plan(
    *,
    project_id: int,
    repo_path: str,
    detected_stack: str,
    dockerfile_path: str | None,
    has_env_file: bool,
    default_port: int = 3000,
    parsed: dict,
) -> dict:
    """
    Build structured DeploymentPlan from project + parsed command.
    Enforces: no execution without env file, no execution without Dockerfile.
    """
    version = parsed.get("version") or "latest"
    image_tag = f"devops-cmd-{project_id}:{version}"
    ports = [f"{default_port}:{default_port}"]
    warnings: list[str] = []

    if not has_env_file:
        warnings.append("No .env file uploaded. Upload env before deployment.")
    if not dockerfile_path:
        warnings.append("No Dockerfile. Project analysis will generate one.")

    return {
        "project_id": project_id,
        "repo_path": repo_path,
        "detected_stack": detected_stack,
        "dockerfile_path": dockerfile_path,
        "image_tag": image_tag,
        "ports": ports,
        "env_injected": has_env_file,
        "action": parsed["action"],
        "version": parsed.get("version"),
        "environments": parsed["environments"],
        "post_steps": parsed["post_steps"],
        "warnings": warnings,
    }
