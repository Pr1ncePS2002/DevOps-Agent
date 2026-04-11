"""Command interpreter — produces structured DeploymentPlan.

Provides two strategies:
- ``interpret_command_deterministic``: Original regex-based parser (kept as fallback).
- ``interpret_command_llm``: Async LLM-powered natural-language parser.
- ``interpret_command``: Async wrapper that tries LLM first, falls back to deterministic.
"""
from __future__ import annotations

import re

import structlog

from app.services.prompts.command_parser import COMMAND_PARSER_SYSTEM_PROMPT

log = structlog.get_logger(__name__)

# ── Deterministic (legacy) ────────────────────────────────────────────────────


def interpret_command_deterministic(text: str) -> dict:
    """Deterministic regex-based parser. Kept as a reliable fallback."""
    normalized = text.strip()
    lowered = normalized.lower()

    action = (
        "deploy"
        if "deploy" in lowered
        else ("rollback" if "rollback" in lowered else "unknown")
    )

    version_match = re.search(r"\bv?(\d+\.\d+(?:\.\d+)*)\b", lowered)
    version = version_match.group(1) if version_match else None

    envs: list[str] = []
    for env in ["dev", "staging", "stage", "prod", "production"]:
        if env in lowered:
            envs.append(
                "staging"
                if env == "stage"
                else ("production" if env == "prod" else env)
            )
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
        "confidence": 1.0,
        "reasoning": "Parsed by deterministic regex engine.",
        "suggested_confirmation": f"{action.capitalize()} to {', '.join(envs)}",
        "interpretation_method": "deterministic",
    }


# Alias so existing callers that import the old name keep working.
interpret_command = interpret_command_deterministic  # noqa: E305


# ── LLM-powered ───────────────────────────────────────────────────────────────

_CONFIDENCE_FALLBACK_THRESHOLD = 0.4

# Valid schema fields returned by the LLM.
_VALID_ACTIONS = {"deploy", "rollback", "restart", "scale", "status", "logs", "unknown"}
_VALID_POST_STEPS = {"run_tests", "smoke_tests", "notify_team", "generate_report"}
_VALID_ENVS = {"staging", "production", "dev"}


def _validate_llm_result(result: dict) -> dict:
    """Clamp / coerce LLM output into a safe shape."""
    action = result.get("action", "unknown")
    if action not in _VALID_ACTIONS:
        action = "unknown"

    version = result.get("version")
    if version is not None:
        version = str(version).lstrip("v").strip() or None

    raw_envs = result.get("environments") or []
    envs = [e for e in raw_envs if e in _VALID_ENVS] or ["staging"]

    raw_steps = result.get("post_steps") or []
    post_steps = [s for s in raw_steps if s in _VALID_POST_STEPS]

    confidence = float(result.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    return {
        "action": action,
        "version": version,
        "environments": envs,
        "post_steps": post_steps,
        "confidence": confidence,
        "reasoning": str(result.get("reasoning", "")).strip(),
        "suggested_confirmation": str(result.get("suggested_confirmation", "")).strip(),
    }


async def interpret_command_llm(text: str) -> dict:
    """Parse *text* using the configured LLM provider.

    Returns a dict matching the command schema.  Raises on LLM failure so the
    caller can apply the deterministic fallback.
    """
    from app.services.llm.factory import get_llm_client  # local import avoids circular deps

    client = get_llm_client()
    log.info("interpret_command_llm_start", text_len=len(text))

    raw = await client.complete_json(
        system_prompt=COMMAND_PARSER_SYSTEM_PROMPT,
        user_prompt=text,
    )

    validated = _validate_llm_result(raw)
    log.info(
        "interpret_command_llm_done",
        action=validated["action"],
        confidence=validated["confidence"],
    )
    return validated


# ── Public async wrapper ──────────────────────────────────────────────────────


async def interpret_command_async(text: str) -> dict:
    """Try LLM first; fall back to deterministic on failure or low confidence.

    Always adds ``"interpretation_method": "llm" | "deterministic"`` to result.
    """
    try:
        result = await interpret_command_llm(text)
        if result["confidence"] < _CONFIDENCE_FALLBACK_THRESHOLD:
            log.warning(
                "llm_low_confidence_fallback",
                confidence=result["confidence"],
                text=text[:80],
            )
            det = interpret_command_deterministic(text)
            det["interpretation_method"] = "deterministic"
            return det

        result["interpretation_method"] = "llm"
        return result

    except Exception as exc:
        log.warning("llm_interpret_failed_fallback", error=str(exc), text=text[:80])
        det = interpret_command_deterministic(text)
        det["interpretation_method"] = "deterministic"
        return det


# ── Deployment plan builder (unchanged) ──────────────────────────────────────


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
    """Build structured DeploymentPlan from project + parsed command.

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
