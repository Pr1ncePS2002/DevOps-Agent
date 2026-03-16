"""
Integration tests for API route endpoints.
Tests real HTTP request/response via FastAPI TestClient.
"""
from __future__ import annotations

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


# ── Health check ──────────────────────────────────────────────────────────────


class TestHealthEndpoint:

    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Project endpoints ─────────────────────────────────────────────────────────


class TestProjectEndpoints:

    def test_list_projects_empty(self, client: TestClient) -> None:
        resp = client.get("/projects")
        assert resp.status_code == 200
        # Could be empty or have leftovers from other tests using same db
        assert isinstance(resp.json(), list)

    def test_register_and_list(self, client: TestClient, local_dir: Path) -> None:
        # Register a project
        resp = client.post("/projects/register", json={
            "project_name": "integration-test",
            "description": "Testing integration",
            "source": {"type": "local", "config": {"path": str(local_dir)}},
            "deployment": {"platform": "docker", "config": {}},
            "env": {},
        })
        assert resp.status_code == 200
        project_id = resp.json()["projectId"]
        assert project_id > 0

        # Verify it appears in the list
        resp = client.get("/projects")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "integration-test" in names

    def test_register_missing_project_name_fails(self, client: TestClient, local_dir: Path) -> None:
        resp = client.post("/projects/register", json={
            "description": "Missing name",
            "source": {"type": "local", "config": {"path": str(local_dir)}},
            "deployment": {"platform": "docker", "config": {}},
            "env": {},
        })
        assert resp.status_code == 422  # Pydantic validation error

    def test_analyze_nonexistent_project(self, client: TestClient) -> None:
        resp = client.get("/projects/99999/analyze")
        assert resp.status_code == 404


# ── Command endpoints ─────────────────────────────────────────────────────────


class TestCommandEndpoints:

    def _create_project(self, client: TestClient) -> int:
        resp = client.post("/projects", json={"name": "cmd-test", "repo_path": "C:/tmp/demo"})
        assert resp.status_code == 200
        return resp.json()["id"]

    def test_parse_deploy_command(self, client: TestClient) -> None:
        pid = self._create_project(client)
        resp = client.post("/commands/parse", json={
            "project_id": pid,
            "text": "Deploy v3.0 to production",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["action"] == "deploy"
        assert body["status"] == "pending_approval"
        assert "production" in body["environments"]

    def test_parse_rollback_command(self, client: TestClient) -> None:
        pid = self._create_project(client)
        resp = client.post("/commands/parse", json={
            "project_id": pid,
            "text": "Rollback in production",
        })
        assert resp.status_code == 200
        assert resp.json()["action"] == "rollback"

    def test_parse_nonexistent_project(self, client: TestClient) -> None:
        resp = client.post("/commands/parse", json={
            "project_id": 99999,
            "text": "Deploy to staging",
        })
        assert resp.status_code == 404

    def test_parse_empty_text_rejected(self, client: TestClient) -> None:
        pid = self._create_project(client)
        resp = client.post("/commands/parse", json={
            "project_id": pid,
            "text": "",
        })
        assert resp.status_code == 422  # min_length=1


# ── Execution endpoints ──────────────────────────────────────────────────────


class TestExecutionEndpoints:

    def test_get_nonexistent_execution(self, client: TestClient) -> None:
        resp = client.get("/executions/99999")
        assert resp.status_code == 404

    def test_rollback_nonexistent_execution(self, client: TestClient) -> None:
        resp = client.post("/executions/99999/rollback")
        assert resp.status_code == 404
