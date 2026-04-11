"""RAG / Plan Advisor service.

Provides two strategies:
- ``advise_plan_deterministic``: Original hardcoded rule-based advisor (fallback).
- ``advise_plan_llm``: Async LLM-powered deployment risk analyser.
- ``advise_plan``: Async public wrapper that tries LLM, falls back to deterministic.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

from app.services.prompts.plan_advisor import PLAN_ADVISOR_SYSTEM_PROMPT

log = structlog.get_logger(__name__)

# ── Risk level / score thresholds ────────────────────────────────────────────

_RISK_THRESHOLDS: list[tuple[int, str]] = [
    (30, "low"),
    (60, "medium"),
    (80, "high"),
    (100, "critical"),
]

_APPROVAL_MAP: dict[str, str] = {
    "low": "auto_approve",
    "medium": "manual_review",
    "high": "manual_review",
    "critical": "block",
}


# ── Deterministic (legacy) ────────────────────────────────────────────────────


def advise_plan_deterministic(
    *,
    action: str,
    environments: list[str],
    post_steps: list[str],
    version: str | None = None,
    project_name: str = "",
) -> dict:
    """Rule-based fallback advisor.  Returns the full advisory dict."""
    warnings: list[str] = []
    recommendations: list[str] = []
    score = 10  # base score

    if "production" in environments:
        score += 30
        warnings.append(
            "Production environment selected: ensure change window and approvals."
        )

    if "run_tests" not in post_steps:
        score += 20
        warnings.append("No tests requested. Consider adding run_tests.")
        recommendations.append("Add run_tests to post_steps before deploying.")

    if "smoke_tests" not in post_steps and "production" in environments:
        score += 10
        warnings.append("No smoke tests configured for a production deploy.")
        recommendations.append("Add smoke_tests to validate the deploy succeeded.")

    if action == "unknown":
        score += 25
        warnings.append(
            "Could not confidently classify action. Review plan carefully."
        )

    if action == "rollback" and not version:
        score += 10
        warnings.append(
            "Rollback requested without a specific version target."
        )
        recommendations.append(
            "Specify the target version explicitly to avoid unexpected rollbacks."
        )

    if not version:
        score += 10

    score = min(score, 100)

    risk_level = "low"
    for threshold, label in _RISK_THRESHOLDS:
        if score <= threshold:
            risk_level = label
            break

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "warnings": warnings,
        "recommendations": recommendations,
        "approval_recommendation": _APPROVAL_MAP[risk_level],
    }


# ── LLM-powered ───────────────────────────────────────────────────────────────

_VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
_VALID_APPROVALS = {"auto_approve", "manual_review", "block"}


def _validate_llm_advisory(raw: dict) -> dict:
    """Clamp / coerce LLM output into a safe shape."""
    risk_level = raw.get("risk_level", "medium")
    if risk_level not in _VALID_RISK_LEVELS:
        risk_level = "medium"

    risk_score = int(raw.get("risk_score", 50))
    risk_score = max(0, min(100, risk_score))

    warnings = [str(w) for w in (raw.get("warnings") or [])]
    recommendations = [str(r) for r in (raw.get("recommendations") or [])]

    approval = raw.get("approval_recommendation", _APPROVAL_MAP[risk_level])
    if approval not in _VALID_APPROVALS:
        approval = _APPROVAL_MAP[risk_level]

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "warnings": warnings,
        "recommendations": recommendations,
        "approval_recommendation": approval,
    }


async def advise_plan_llm(
    *,
    action: str,
    environments: list[str],
    post_steps: list[str],
    version: str | None = None,
    project_name: str = "",
) -> dict:
    """Analyse a deployment plan using the configured LLM provider.

    Returns:
        dict with keys: risk_level, risk_score, warnings, recommendations,
        approval_recommendation.

    Raises on LLM failure so the caller can apply the deterministic fallback.
    """
    from app.services.llm.factory import get_llm_client  # local import avoids circular deps

    client = get_llm_client()

    day_of_week = datetime.now(timezone.utc).strftime("%A")

    user_prompt = json.dumps(
        {
            "action": action,
            "environments": environments,
            "version": version,
            "post_steps": post_steps,
            "project_name": project_name,
            "day_of_week": day_of_week,
        },
        indent=2,
    )

    log.info(
        "advise_plan_llm_start",
        action=action,
        environments=environments,
        post_steps=post_steps,
        project_name=project_name,
    )

    raw = await client.complete_json(
        system_prompt=PLAN_ADVISOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    result = _validate_llm_advisory(raw)
    log.info(
        "advise_plan_llm_done",
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        warning_count=len(result["warnings"]),
    )
    return result


# ── Public async wrapper ──────────────────────────────────────────────────────


async def advise_plan(
    *,
    action: str,
    environments: list[str],
    post_steps: list[str],
    version: str | None = None,
    project_name: str = "",
) -> dict:
    """Try LLM advisor first; fall back to deterministic on any failure.

    Returns:
        dict with keys: risk_level, risk_score, warnings (list[str]),
        recommendations (list[str]), approval_recommendation.
    """
    try:
        return await advise_plan_llm(
            action=action,
            environments=environments,
            post_steps=post_steps,
            version=version,
            project_name=project_name,
        )
    except Exception as exc:
        log.warning(
            "advise_plan_llm_failed_fallback",
            error=str(exc),
            action=action,
            environments=environments,
        )
        return advise_plan_deterministic(
            action=action,
            environments=environments,
            post_steps=post_steps,
            version=version,
            project_name=project_name,
        )
