"""Provider connect routes — Vercel & Render token validation + resource listing."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import httpx

from app.common.logging import logger
from app.services.env_storage import _get_fernet


router = APIRouter()

log = logger.bind(component="providers")


# ── Request / Response schemas ────────────────────────────────────────────────


class VercelConnectRequest(BaseModel):
    token: str


class VercelProject(BaseModel):
    id: str
    name: str
    framework: str | None = None
    updated_at: int | None = None


class VercelConnectResponse(BaseModel):
    user: str
    team_id: str | None = None
    projects: list[VercelProject]


class RenderConnectRequest(BaseModel):
    api_key: str


class RenderService(BaseModel):
    id: str
    name: str
    type: str
    url: str | None = None


class RenderConnectResponse(BaseModel):
    services: list[RenderService]


class EncryptTokenRequest(BaseModel):
    provider: str
    token: str


class EncryptTokenResponse(BaseModel):
    encrypted: str | None = None
    stored: bool = False


# ── Vercel routes ─────────────────────────────────────────────────────────────


@router.post("/vercel/connect", response_model=VercelConnectResponse)
def vercel_connect(payload: VercelConnectRequest) -> VercelConnectResponse:
    """
    Validate a Vercel token and list the user's projects.
    The frontend uses this to auto-populate VERCEL_PROJECT_ID and VERCEL_TEAM_ID.
    """
    headers = {
        "Authorization": f"Bearer {payload.token}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            # 1. Get user info (validates the token)
            user_res = client.get("https://api.vercel.com/v2/user", headers=headers)
            if user_res.status_code == 403:
                raise HTTPException(status_code=401, detail="Invalid Vercel token")
            user_res.raise_for_status()
            user_data = user_res.json().get("user", {})
            username = user_data.get("username", user_data.get("name", "unknown"))

            # Detect team context
            team_id: str | None = None
            teams_res = client.get("https://api.vercel.com/v2/teams", headers=headers)
            if teams_res.status_code == 200:
                teams = teams_res.json().get("teams", [])
                if teams:
                    team_id = teams[0].get("id")

            # 2. List projects
            params: dict = {"limit": "50"}
            if team_id:
                params["teamId"] = team_id

            proj_res = client.get(
                "https://api.vercel.com/v9/projects",
                headers=headers,
                params=params,
            )
            proj_res.raise_for_status()
            raw_projects = proj_res.json().get("projects", [])

            projects = [
                VercelProject(
                    id=p["id"],
                    name=p.get("name", ""),
                    framework=p.get("framework"),
                    updated_at=p.get("updatedAt"),
                )
                for p in raw_projects
            ]

        return VercelConnectResponse(user=username, team_id=team_id, projects=projects)

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        log.warning("vercel_connect_failed", status=e.response.status_code)
        raise HTTPException(status_code=e.response.status_code, detail="Vercel API error")
    except Exception as e:
        log.exception("vercel_connect_error", error=str(e))
        raise HTTPException(status_code=502, detail="Failed to connect to Vercel API")


# ── Render routes ─────────────────────────────────────────────────────────────


@router.post("/render/connect", response_model=RenderConnectResponse)
def render_connect(payload: RenderConnectRequest) -> RenderConnectResponse:
    """
    Validate a Render API key and list the user's services.
    The frontend uses this to auto-populate RENDER_SERVICE_ID.
    """
    headers = {
        "Authorization": f"Bearer {payload.api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            svc_res = client.get("https://api.render.com/v1/services", headers=headers)
            if svc_res.status_code in (401, 403):
                raise HTTPException(status_code=401, detail="Invalid Render API key")
            svc_res.raise_for_status()
            raw_services = svc_res.json()

            services = [
                RenderService(
                    id=s.get("service", s).get("id", s.get("id", "")),
                    name=s.get("service", s).get("name", s.get("name", "")),
                    type=s.get("service", s).get("type", s.get("type", "")),
                    url=s.get("service", s).get("serviceDetails", {}).get("url"),
                )
                for s in raw_services
            ]

        return RenderConnectResponse(services=services)

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        log.warning("render_connect_failed", status=e.response.status_code)
        raise HTTPException(status_code=e.response.status_code, detail="Render API error")
    except Exception as e:
        log.exception("render_connect_error", error=str(e))
        raise HTTPException(status_code=502, detail="Failed to connect to Render API")


# ── Token encryption helper ──────────────────────────────────────────────────


@router.post("/encrypt-token", response_model=EncryptTokenResponse)
def encrypt_token(payload: EncryptTokenRequest) -> EncryptTokenResponse:
    """
    Encrypt a provider token using the server's Fernet key.
    Returns the encrypted string (never logs the plaintext).
    """
    fernet = _get_fernet()
    if not fernet:
        raise HTTPException(
            status_code=400,
            detail="ENCRYPTION_KEY not configured on the server. Tokens cannot be encrypted at rest.",
        )

    encrypted = fernet.encrypt(payload.token.encode()).decode()
    return EncryptTokenResponse(encrypted=encrypted, stored=True)
