from __future__ import annotations

import re


def interpret_command(text: str) -> dict:
    """Deterministic MVP parser.

    This intentionally avoids executing anything and produces a plan-like dict.
    Later: replace with LLM-backed structured extraction behind the same interface.
    """

    normalized = text.strip()
    lowered = normalized.lower()

    action = "deploy" if "deploy" in lowered else "unknown"

    # version patterns: v1.6, 1.6, release-1.6
    version_match = re.search(r"\bv?(\d+\.\d+(?:\.\d+)*)\b", lowered)
    version = version_match.group(1) if version_match else None

    envs: list[str] = []
    for env in ["dev", "staging", "stage", "prod", "production"]:
        if env in lowered:
            envs.append("staging" if env == "stage" else ("production" if env == "prod" else env))

    if not envs:
        envs = ["staging"]  # safe default for MVP

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
