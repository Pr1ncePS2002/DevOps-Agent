"""
Unit tests for the command interpreter module.
Tests both `interpret_command` and `build_deployment_plan`.
"""
from __future__ import annotations

import pytest

from app.services.command_interpreter import build_deployment_plan, interpret_command


# ── interpret_command ─────────────────────────────────────────────────────────


class TestInterpretCommand:
    """Covers parsing of natural-language deployment commands."""

    def test_deploy_action_detected(self) -> None:
        result = interpret_command("Deploy the app to staging")
        assert result["action"] == "deploy"

    def test_rollback_action_detected(self) -> None:
        result = interpret_command("Rollback in production")
        assert result["action"] == "rollback"

    def test_unknown_action_fallback(self) -> None:
        result = interpret_command("Check the server logs")
        assert result["action"] == "unknown"

    def test_version_extracted(self) -> None:
        result = interpret_command("Deploy v1.6.3 to staging")
        assert result["version"] == "1.6.3"

    def test_version_without_v_prefix(self) -> None:
        result = interpret_command("Deploy 2.0 to prod")
        assert result["version"] == "2.0"

    def test_no_version_returns_none(self) -> None:
        result = interpret_command("Deploy to staging")
        assert result["version"] is None

    def test_staging_environment_parsed(self) -> None:
        result = interpret_command("Deploy to staging")
        assert "staging" in result["environments"]

    def test_prod_normalized_to_production(self) -> None:
        result = interpret_command("Deploy to prod")
        assert "production" in result["environments"]

    def test_stage_normalized_to_staging(self) -> None:
        result = interpret_command("Deploy to stage")
        assert "staging" in result["environments"]

    def test_multiple_environments(self) -> None:
        result = interpret_command("Deploy to dev and production")
        assert "dev" in result["environments"]
        assert "production" in result["environments"]

    def test_default_environment_is_staging(self) -> None:
        result = interpret_command("Deploy the app")
        assert result["environments"] == ["staging"]

    def test_post_step_test_detected(self) -> None:
        result = interpret_command("Deploy and run tests")
        assert "run_tests" in result["post_steps"]

    def test_post_step_smoke_detected(self) -> None:
        result = interpret_command("Deploy and run smoke tests")
        assert "smoke_tests" in result["post_steps"]
        # 'test' is also a substring of 'smoke tests'
        assert "run_tests" in result["post_steps"]

    def test_no_post_steps_by_default(self) -> None:
        result = interpret_command("Deploy to staging")
        assert result["post_steps"] == []

    def test_whitespace_handling(self) -> None:
        result = interpret_command("   deploy to staging   ")
        assert result["action"] == "deploy"

    def test_case_insensitivity(self) -> None:
        result = interpret_command("DEPLOY TO PRODUCTION")
        assert result["action"] == "deploy"
        assert "production" in result["environments"]


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
        required = ["project_id", "repo_path", "detected_stack", "dockerfile_path",
                     "image_tag", "ports", "env_injected", "action", "version",
                     "environments", "post_steps", "warnings"]
        for key in required:
            assert key in plan, f"Missing key: {key}"
