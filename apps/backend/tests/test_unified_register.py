"""
Tests for the unified POST /projects/register endpoint.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def local_dir(tmp_path: Path) -> Path:
    """Create a minimal local project directory."""
    (tmp_path / "main.py").write_text("print('hello')")
    return tmp_path


# ── Source × Platform compatibility ──────────────────────────────────────────


def test_register_local_docker(client: TestClient, local_dir: Path) -> None:
    """local source + docker platform — happy path."""
    resp = client.post(
        "/projects/register",
        json={
            "project_name": "test-local-docker",
            "description": "A test project",
            "source": {
                "type": "local",
                "config": {"path": str(local_dir)},
            },
            "deployment": {
                "platform": "docker",
                "config": {},
            },
            "env": {
                "LOCAL_PATH": str(local_dir),
                "DOCKERFILE": str(local_dir / "Dockerfile"),
            },
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["projectId"] > 0
    assert body["name"] == "test-local-docker"
    assert body["deploymentPlatform"] == "docker"
    assert "workspacePath" in body


def test_register_local_local(client: TestClient, local_dir: Path) -> None:
    """local source + local platform — happy path."""
    resp = client.post(
        "/projects/register",
        json={
            "project_name": "test-local-local",
            "description": "",
            "source": {
                "type": "local",
                "config": {"path": str(local_dir)},
            },
            "deployment": {
                "platform": "local",
                "config": {},
            },
            "env": {"LOCAL_PATH": str(local_dir)},
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["deploymentPlatform"] == "local"


def test_register_local_vercel_rejected(client: TestClient, local_dir: Path) -> None:
    """local source + vercel platform — must be rejected (422 Pydantic / service check)."""
    resp = client.post(
        "/projects/register",
        json={
            "project_name": "bad-combo",
            "description": "",
            "source": {
                "type": "local",
                "config": {"path": str(local_dir)},
            },
            "deployment": {
                "platform": "vercel",
                "config": {},
            },
            "env": {},
        },
    )
    # Service raises ValueError → 422
    assert resp.status_code in (400, 422), resp.text


def test_register_env_warnings_returned(client: TestClient, local_dir: Path) -> None:
    """
    Missing required env keys produce warnings but do NOT block registration.
    """
    resp = client.post(
        "/projects/register",
        json={
            "project_name": "env-warning-test",
            "description": "",
            "source": {
                "type": "local",
                "config": {"path": str(local_dir)},
            },
            "deployment": {
                "platform": "docker",
                "config": {},
            },
            "env": {},  # Missing LOCAL_PATH and DOCKERFILE
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["projectId"] > 0
    # envWarnings should contain at least one warning about missing keys
    assert len(body.get("envWarnings", [])) > 0


def test_register_invalid_path_returns_400(client: TestClient) -> None:
    """Non-existent local path should return 400."""
    resp = client.post(
        "/projects/register",
        json={
            "project_name": "bad-path",
            "description": "",
            "source": {
                "type": "local",
                "config": {"path": "/nonexistent/path/zzzz"},
            },
            "deployment": {
                "platform": "docker",
                "config": {},
            },
            "env": {},
        },
    )
    assert resp.status_code == 400, resp.text


# ── Legacy endpoint still works ───────────────────────────────────────────────


def test_legacy_create_project(client: TestClient) -> None:
    """Legacy POST /projects still works for backward compat (used by test_command_parse.py)."""
    resp = client.post(
        "/projects",
        json={"name": "legacy-demo", "repo_path": "C:/tmp/demo"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "legacy-demo"
    assert "deployment_platform" in body
