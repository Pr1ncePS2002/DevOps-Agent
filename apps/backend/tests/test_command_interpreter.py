"""
Unit tests for the command interpreter module.
Tests interpret_command_deterministic, build_deployment_plan,
and the async LLM-powered wrapper (interpret_command_async).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.command_interpreter import (
    build_deployment_plan,
    interpret_command_async,
    interpret_command_deterministic,
)


# ── interpret_command_deterministic ───────────────────────────────────────────


class TestInterpretCommandDeterministic:
    """Covers the regex-based deterministic parser (fallback)."""

    def test_deploy_action_detected(self) -> None:
        result = interpret_command_deterministic("Deploy the app to staging")
        assert result["action"] == "deploy"

    def test_rollback_action_detected(self) -> None:
        result = interpret_command_deterministic("Rollback in production")
        assert result["action"] == "rollback"

    def test_unknown_action_fallback(self) -> None:
        result = interpret_command_deterministic("Check the server logs")
        assert result["action"] == "unknown"

    def test_version_extracted(self) -> None:
        result = interpret_command_deterministic("Deploy v1.6.3 to staging")
        assert result["version"] == "1.6.3"

    def test_version_without_v_prefix(self) -> None:
        result = interpret_command_deterministic("Deploy 2.0 to prod")
        assert result["version"] == "2.0"

    def test_no_version_returns_none(self) -> None:
        result = interpret_command_deterministic("Deploy to staging")
        assert result["version"] is None

    def test_staging_environment_parsed(self) -> None:
        result = interpret_command_deterministic("Deploy to staging")
        assert "staging" in result["environments"]

    def test_prod_normalized_to_production(self) -> None:
        result = interpret_command_deterministic("Deploy to prod")
        assert "production" in result["environments"]

    def test_stage_normalized_to_staging(self) -> None:
        result = interpret_command_deterministic("Deploy to stage")
        assert "staging" in result["environments"]

    def test_multiple_environments(self) -> None:
        result = interpret_command_deterministic("Deploy to dev and production")
        assert "dev" in result["environments"]
        assert "production" in result["environments"]

    def test_default_environment_is_staging(self) -> None:
        result = interpret_command_deterministic("Deploy the app")
        assert result["environments"] == ["staging"]

    def test_post_step_test_detected(self) -> None:
        result = interpret_command_deterministic("Deploy and run tests")
        assert "run_tests" in result["post_steps"]

    def test_post_step_smoke_detected(self) -> None:
        result = interpret_command_deterministic("Deploy and run smoke tests")
        assert "smoke_tests" in result["post_steps"]
        # 'test' is also a substring of 'smoke tests'
        assert "run_tests" in result["post_steps"]

    def test_no_post_steps_by_default(self) -> None:
        result = interpret_command_deterministic("Deploy to staging")
        assert result["post_steps"] == []

    def test_whitespace_handling(self) -> None:
        result = interpret_command_deterministic("   deploy to staging   ")
        assert result["action"] == "deploy"

    def test_case_insensitivity(self) -> None:
        result = interpret_command_deterministic("DEPLOY TO PRODUCTION")
        assert result["action"] == "deploy"
        assert "production" in result["environments"]

    def test_returns_interpretation_method_deterministic(self) -> None:
        result = interpret_command_deterministic("Deploy to staging")
        assert result["interpretation_method"] == "deterministic"


# ── backward-compat alias ─────────────────────────────────────────────────────


class TestInterpretCommandAlias:
    """The old `interpret_command` name must still resolve."""

    def test_alias_works(self) -> None:
        from app.services.command_interpreter import interpret_command

        result = interpret_command("Deploy to staging")
        assert result["action"] == "deploy"


# ── build_deployment_plan ─────────────────────────────────────────────────────


class TestBuildDeploymentPlan:
    """Covers construction of deployment plan dicts."""

    @pytest.fixture
    def base_parsed(self) -> dict:
        return {
            "action": "deploy",
            "version": "1.0",
            "environments": ["staging"],
            "post_steps": [],
        }

    def test_image_tag_includes_project_id(self, base_parsed: dict) -> None:
        plan = build_deployment_plan(
            project_id=42,
            repo_path="/tmp/repo",
            detected_stack="node",
            dockerfile_path="Dockerfile",
            has_env_file=True,
            parsed=base_parsed,
        )
        assert "42" in plan["image_tag"]
        assert "1.0" in plan["image_tag"]

    def test_latest_used_when_no_version(self, base_parsed: dict) -> None:
        base_parsed["version"] = None
        plan = build_deployment_plan(
            project_id=1,
            repo_path="/tmp",
            detected_stack="python",
            dockerfile_path="Dockerfile",
            has_env_file=True,
            parsed=base_parsed,
        )
        assert "latest" in plan["image_tag"]

    def test_warning_when_no_env_file(self, base_parsed: dict) -> None:
        plan = build_deployment_plan(
            project_id=1,
            repo_path="/tmp",
            detected_stack="node",
            dockerfile_path="Dockerfile",
            has_env_file=False,
            parsed=base_parsed,
        )
        assert any("env" in w.lower() for w in plan["warnings"])

    def test_warning_when_no_dockerfile(self, base_parsed: dict) -> None:
        plan = build_deployment_plan(
            project_id=1,
            repo_path="/tmp",
            detected_stack="node",
            dockerfile_path=None,
            has_env_file=True,
            parsed=base_parsed,
        )
        assert any("dockerfile" in w.lower() for w in plan["warnings"])

    def test_ports_default(self, base_parsed: dict) -> None:
        plan = build_deployment_plan(
            project_id=1,
            repo_path="/tmp",
            detected_stack="node",
            dockerfile_path="Dockerfile",
            has_env_file=True,
            default_port=3000,
            parsed=base_parsed,
        )
        assert "3000:3000" in plan["ports"]

    def test_all_fields_present(self, base_parsed: dict) -> None:
        plan = build_deployment_plan(
            project_id=1,
            repo_path="/tmp",
            detected_stack="node",
            dockerfile_path="Dockerfile",
            has_env_file=True,
            parsed=base_parsed,
        )
        required = [
            "project_id",
            "repo_path",
            "detected_stack",
            "dockerfile_path",
            "image_tag",
            "ports",
            "env_injected",
            "action",
            "version",
            "environments",
            "post_steps",
            "warnings",
        ]
        for key in required:
            assert key in plan, f"Missing key: {key}"


# ── interpret_command_async (LLM wrapper) ─────────────────────────────────────


class TestInterpretCommandAsync:
    """Tests the async LLM wrapper with mocked LLM client."""

    @pytest.mark.asyncio
    async def test_llm_response_is_properly_parsed(self) -> None:
        """LLM result is returned when confidence >= threshold."""
        llm_reply = {
            "action": "deploy",
            "version": "2.1",
            "environments": ["production"],
            "post_steps": ["smoke_tests"],
            "confidence": 0.95,
            "reasoning": "Clear deploy command targeting production.",
            "suggested_confirmation": "Deploy v2.1 to production, then run smoke tests",
        }

        with patch(
            "app.services.command_interpreter.interpret_command_llm",
            new=AsyncMock(return_value=llm_reply),
        ):
            result = await interpret_command_async("ship v2.1 to production and run smoke tests")

        assert result["action"] == "deploy"
        assert result["version"] == "2.1"
        assert "production" in result["environments"]
        assert result["confidence"] == 0.95
        assert result["interpretation_method"] == "llm"

    @pytest.mark.asyncio
    async def test_fallback_triggers_on_llm_failure(self) -> None:
        """Deterministic fallback is used when LLM raises an exception."""
        with patch(
            "app.services.command_interpreter.interpret_command_llm",
            new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
        ):
            result = await interpret_command_async("Deploy to staging")

        assert result["action"] == "deploy"
        assert result["interpretation_method"] == "deterministic"

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_fallback(self) -> None:
        """Deterministic fallback is used when LLM confidence < 0.4."""
        low_conf_reply = {
            "action": "unknown",
            "version": None,
            "environments": ["staging"],
            "post_steps": [],
            "confidence": 0.1,
            "reasoning": "Too vague.",
            "suggested_confirmation": "Unable to determine action",
        }

        with patch(
            "app.services.command_interpreter.interpret_command_llm",
            new=AsyncMock(return_value=low_conf_reply),
        ):
            result = await interpret_command_async("do the thing")

        assert result["interpretation_method"] == "deterministic"

    @pytest.mark.asyncio
    async def test_confidence_and_reasoning_present_in_response(self) -> None:
        """Both confidence and reasoning fields are present in every response."""
        llm_reply = {
            "action": "rollback",
            "version": "1.9",
            "environments": ["production"],
            "post_steps": [],
            "confidence": 0.98,
            "reasoning": "Rollback command detected.",
            "suggested_confirmation": "Rollback production to v1.9",
        }

        with patch(
            "app.services.command_interpreter.interpret_command_llm",
            new=AsyncMock(return_value=llm_reply),
        ):
            result = await interpret_command_async("rollback production to v1.9")

        assert "confidence" in result
        assert "reasoning" in result
        assert "suggested_confirmation" in result
        assert isinstance(result["confidence"], float)
