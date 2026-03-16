"""Deployment status polling routes — Vercel & Render real-time status."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.common.logging import logger
from app.services.deployers import get_deployer


router = APIRouter()

log = logger.bind(component="deploy-status")


class DeployStatusResponse(BaseModel):
    provider: str
    deployment_id: str
    status: str
    message: str
    url: str | None = None
    is_terminal: bool = False


# Map provider-specific states to a normalised set
VERCEL_STATE_MAP = {
    "QUEUED": "queued",
    "BUILDING": "building",
    "INITIALIZING": "building",
    "DEPLOYING": "deploying",
    "READY": "live",
    "ERROR": "failed",
    "CANCELED": "failed",
}

RENDER_STATE_MAP = {
    "created": "queued",
    "build_in_progress": "building",
    "update_in_progress": "deploying",
    "pre_deploy_in_progress": "deploying",
    "live": "live",
    "deactivated": "failed",
    "build_failed": "failed",
    "update_failed": "failed",
    "canceled": "failed",
    "pre_deploy_failed": "failed",
}

TERMINAL_STATES = {"live", "failed"}


@router.get("/status/{provider}/{deployment_id}", response_model=DeployStatusResponse)
def get_deploy_status(provider: str, deployment_id: str) -> DeployStatusResponse:
    """
    Poll deployment status for Vercel or Render.
    Returns normalised status: queued | building | deploying | live | failed.
    Frontend polls this every 5s until is_terminal=True.
    """
    provider_lower = provider.lower()

    if provider_lower not in ("vercel", "render"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    try:
        deployer = get_deployer(provider_lower)
        result = deployer.get_deployment_status(deployment_id)

        if provider_lower == "vercel":
            raw_state = (result.metadata or {}).get("state", "UNKNOWN")
            normalised = VERCEL_STATE_MAP.get(raw_state, "building")
        else:
            raw_state = (result.metadata or {}).get("status", "unknown")
            normalised = RENDER_STATE_MAP.get(raw_state, "building")

        return DeployStatusResponse(
            provider=provider_lower,
            deployment_id=deployment_id,
            status=normalised,
            message=result.message,
            url=result.deployment_url,
            is_terminal=normalised in TERMINAL_STATES,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.exception("deploy_status_error", provider=provider_lower, error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to check status: {e}")
