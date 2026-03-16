"""
ProjectRegistrationService — single entry point for all project registration.

Replaces the scattered logic in:
  - app/api/routes/projects.py register_project_endpoint()
  - app/api/routes/projects.py create_project_endpoint()
  - app/services/project_registration.py (still used internally)
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlmodel import Session

from app.common.logging import logger
from app.persistence.repositories import create_project
from app.services.project_analysis import analyze_project
from app.services.project_registration import register_local, register_github
from app.services.registration.env_matrix import validate_env, validate_platform_compat
from app.services.registration.schemas import (
    RegisterProjectPayload,
    RegisterProjectResponse,
)

_log = logger.bind(component="registration-service")


class ProjectRegistrationService:
    """
    Encapsulates the full registration pipeline:
      1. Validate source × platform compatibility
      2. Resolve / clone workspace
      3. Analyse project stack (auto-generate Dockerfile if missing)
      4. Warn on missing env keys
      5. Persist Project record with all new fields
    """

    def register(
        self, *, session, payload: RegisterProjectPayload
    ) -> RegisterProjectResponse:
        source_type = payload.source.type
        platform = payload.deployment.platform

        # 1. Platform compat check (raises ValueError → 422)
        validate_platform_compat(source_type, platform)

        # 2. Resolve/clone workspace using typed_config
        cfg = payload.source.typed_config
        if source_type == "local":
            workspace_path, name = register_local(cfg.path)  # type: ignore[union-attr]
        else:
            workspace_path, name = register_github(cfg.repo_url)  # type: ignore[union-attr]

        _log.info("workspace_resolved", path=str(workspace_path), name=name)

        # Override name with user-provided project_name
        name = payload.project_name

        # 3. Analyse stack
        analysis = analyze_project(workspace_path)

        # 4. Env warnings (non-blocking)
        env_warnings = validate_env(payload.env, source_type, platform)
        if env_warnings:
            _log.warning("missing_env_keys", keys=env_warnings, project=name)

        # 5. Determine repo fields
        repo_path: str | None = None
        repo_url: str | None = None
        branch: str | None = None

        if source_type == "local":
            repo_path = str(workspace_path)
        else:
            cfg_gh = payload.source.typed_config
            repo_url = cfg_gh.repo_url  # type: ignore[union-attr]
            branch = cfg_gh.branch  # type: ignore[union-attr]

        # 6. Persist
        project = create_project(
            session,
            name=name,
            description=payload.description,
            source_type=source_type,
            repo_path=repo_path,
            repo_url=repo_url,
            branch=branch,
            workspace_path=str(workspace_path),
            detected_stack=analysis["detected_stack"],
            dockerfile_path=analysis.get("dockerfile_path"),
            deployment_platform=platform,
            deployment_config_json=json.dumps(payload.deployment.config),
            env_config_json=json.dumps(list(payload.env.keys())),
        )

        _log.info("project_registered", project_id=project.id, platform=platform)

        return RegisterProjectResponse(
            project_id=project.id or 0,
            name=project.name,
            workspace_path=str(workspace_path),
            detected_stack=analysis["detected_stack"],
            dockerfile_path=analysis.get("dockerfile_path"),
            dockerfile_generated=analysis.get("dockerfile_generated", False),
            deployment_platform=platform,
            env_warnings=env_warnings,
        )
