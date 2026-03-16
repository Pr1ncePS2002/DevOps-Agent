"""
Unified Pydantic schemas for project registration.

A single normalised payload replaces the two old schemas:
  - RegisterRequest  {source_type, path_or_url}
  - ProjectCreateRequest {name, repo_path, repo_url}
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


# ── Source configs ────────────────────────────────────────────────────────────

class LocalSourceConfig(BaseModel):
    path: str = Field(..., min_length=1, max_length=2000)

    @model_validator(mode="after")
    def _strip_quotes(self) -> "LocalSourceConfig":
        """Remove accidental surrounding quotes the UI may add."""
        self.path = self.path.strip().strip('"').strip("'").strip()
        return self


class GithubSourceConfig(BaseModel):
    repo_url: str = Field(..., alias="repoUrl", min_length=1, max_length=2000)
    branch: str = Field(default="main", max_length=200)
    access_token: str | None = Field(default=None, alias="accessToken")

    model_config = ConfigDict(populate_by_name=True)


# ── Source / Deployment blocks ───────────────────────────────────────────────

class SourceBlock(BaseModel):
    """
    Accepts the flat dict the frontend sends for config.
    We coerce it into the right typed config inside the validator.
    """
    type: Literal["local", "github"]
    config: dict[str, Any]  # accept raw dict, coerce below

    # Resolved typed config (not part of parsed JSON input)
    _resolved_local: LocalSourceConfig | None = None
    _resolved_github: GithubSourceConfig | None = None

    @model_validator(mode="after")
    def _coerce_config(self) -> "SourceBlock":
        if self.type == "local":
            self._resolved_local = LocalSourceConfig(**self.config)
        else:
            self._resolved_github = GithubSourceConfig(**self.config)
        return self

    @property
    def typed_config(self) -> LocalSourceConfig | GithubSourceConfig:
        return self._resolved_local or self._resolved_github  # type: ignore[return-value]


class DeploymentBlock(BaseModel):
    platform: Literal["local", "docker", "vercel", "render"]
    config: dict[str, str] = Field(default_factory=dict)


# ── Top-level payload ─────────────────────────────────────────────────────────

class RegisterProjectPayload(BaseModel):
    """
    Unified project registration payload.

    Accepts camelCase from the frontend (projectName, etc.)
    and maps to Python snake_case fields automatically.
    """
    model_config = ConfigDict(
        alias_generator=to_camel,   # projectName ↔ project_name
        populate_by_name=True,       # also accept snake_case if needed
    )

    project_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    source: SourceBlock
    deployment: DeploymentBlock
    env: dict[str, str] = Field(default_factory=dict)


# ── Response ──────────────────────────────────────────────────────────────────

class RegisterProjectResponse(BaseModel):
    """Response shape — camelCase for the frontend."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    project_id: int
    name: str
    workspace_path: str
    detected_stack: str
    dockerfile_path: str | None
    dockerfile_generated: bool
    deployment_platform: str
    env_warnings: list[str] = Field(default_factory=list)
