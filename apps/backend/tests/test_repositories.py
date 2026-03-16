"""
Unit tests for the persistence layer: repositories and models.
Uses an in-memory SQLite database for isolation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.persistence.models import Deployment, Execution, Plan, Project
from app.persistence import repositories as repo


@pytest.fixture
def session():
    """Provide a clean in-memory SQLite session per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as s:
        yield s


# ── Project CRUD ──────────────────────────────────────────────────────────────


class TestProjectCRUD:

    def test_create_project_defaults(self, session: Session) -> None:
        p = repo.create_project(session, name="test-proj")
        assert p.id is not None
        assert p.name == "test-proj"
        assert p.source_type == "local"
        assert p.deployment_platform == "docker"

    def test_create_project_with_all_fields(self, session: Session) -> None:
        p = repo.create_project(
            session,
            name="full-proj",
            source_type="github",
            description="A full test",
            repo_url="https://github.com/user/repo",
            branch="main",
            deployment_platform="vercel",
            deployment_config_json='{"team": "my-team"}',
            env_config_json='["API_KEY", "DB_URL"]',
        )
        assert p.source_type == "github"
        assert p.deployment_platform == "vercel"
        assert json.loads(p.deployment_config_json) == {"team": "my-team"}

    def test_list_projects_ordered_by_created_desc(self, session: Session) -> None:
        repo.create_project(session, name="first")
        repo.create_project(session, name="second")
        projects = repo.list_projects(session)
        assert len(projects) == 2
        assert projects[0].name == "second"  # latest first

    def test_get_project_found(self, session: Session) -> None:
        p = repo.create_project(session, name="findme")
        found = repo.get_project(session, p.id)
        assert found is not None
        assert found.name == "findme"

    def test_get_project_not_found(self, session: Session) -> None:
        assert repo.get_project(session, 99999) is None

    def test_update_project_fields(self, session: Session) -> None:
        p = repo.create_project(session, name="update-test")
        updated = repo.update_project(
            session, p,
            detected_stack="python",
            has_env_file=True,
            last_known_good_tag="v1.0",
        )
        assert updated.detected_stack == "python"
        assert updated.has_env_file is True
        assert updated.last_known_good_tag == "v1.0"

    def test_update_project_none_keeps_old_value(self, session: Session) -> None:
        p = repo.create_project(session, name="partial", detected_stack="node")
        updated = repo.update_project(session, p, detected_stack=None)
        # None means "don't update", so old value should remain
        assert updated.detected_stack == "node"


# ── Plan CRUD ─────────────────────────────────────────────────────────────────


class TestPlanCRUD:

    def test_create_plan_stores_json(self, session: Session) -> None:
        p = repo.create_project(session, name="plan-proj")
        plan = repo.create_plan(
            session,
            project_id=p.id,
            raw_command="Deploy v2.0 to production",
            action="deploy",
            version="2.0",
            environments=["production"],
            post_steps=["run_tests"],
            warnings=["No Dockerfile"],
        )
        assert plan.id is not None
        assert plan.status == "pending_approval"
        assert json.loads(plan.environments_json) == ["production"]
        assert json.loads(plan.post_steps_json) == ["run_tests"]

    def test_update_plan_status(self, session: Session) -> None:
        p = repo.create_project(session, name="status-proj")
        plan = repo.create_plan(
            session,
            project_id=p.id,
            raw_command="deploy",
            action="deploy",
            version=None,
            environments=["staging"],
            post_steps=[],
            warnings=[],
        )
        updated = repo.update_plan_status(session, plan, "approved")
        assert updated.status == "approved"

    def test_get_plan_not_found(self, session: Session) -> None:
        assert repo.get_plan(session, 99999) is None


# ── Execution CRUD ────────────────────────────────────────────────────────────


class TestExecutionCRUD:

    def test_create_execution(self, session: Session) -> None:
        p = repo.create_project(session, name="exec-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        assert ex.status == "queued"
        assert ex.plan_id == plan.id

    def test_append_execution_log(self, session: Session) -> None:
        p = repo.create_project(session, name="log-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        repo.append_execution_log(session, ex, "Line 1")
        repo.append_execution_log(session, ex, "Line 2")
        assert "Line 1" in ex.logs
        assert "Line 2" in ex.logs

    def test_set_execution_status_running_sets_started_at(self, session: Session) -> None:
        p = repo.create_project(session, name="started-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        assert ex.started_at is None
        repo.set_execution_status(session, ex, "running")
        assert ex.started_at is not None

    def test_set_execution_status_failed_sets_finished_at(self, session: Session) -> None:
        p = repo.create_project(session, name="finished-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        repo.set_execution_status(session, ex, "failed")
        assert ex.finished_at is not None

    def test_set_execution_status_succeeded(self, session: Session) -> None:
        p = repo.create_project(session, name="succ-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        # Must follow valid transition chain: queued → running → succeeded
        repo.set_execution_status(session, ex, "running")
        repo.set_execution_status(session, ex, "succeeded")
        assert ex.finished_at is not None

    def test_invalid_execution_transition_raises(self, session: Session) -> None:
        """Verify the state machine rejects invalid transitions."""
        import pytest as _pt
        p = repo.create_project(session, name="invalid-trans-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        ex = repo.create_execution(session, plan.id)
        with _pt.raises(ValueError, match="Invalid execution transition"):
            # queued → succeeded is not allowed (must go through running first)
            repo.set_execution_status(session, ex, "succeeded")

    def test_invalid_plan_transition_raises(self, session: Session) -> None:
        """Verify the state machine rejects invalid plan transitions."""
        import pytest as _pt
        p = repo.create_project(session, name="invalid-plan-proj")
        plan = repo.create_plan(
            session, project_id=p.id, raw_command="deploy",
            action="deploy", version=None, environments=["staging"],
            post_steps=[], warnings=[],
        )
        with _pt.raises(ValueError, match="Invalid plan transition"):
            # pending_approval → running is not allowed (must go through approved first)
            repo.update_plan_status(session, plan, "running")


# ── Deployment CRUD ───────────────────────────────────────────────────────────


class TestDeploymentCRUD:

    def test_create_deployment(self, session: Session) -> None:
        p = repo.create_project(session, name="deploy-proj")
        d = repo.create_deployment(session, project_id=p.id, status="pending")
        assert d.id is not None
        assert d.status == "pending"

    def test_get_latest_deployment(self, session: Session) -> None:
        import time as _time
        p = repo.create_project(session, name="latest-proj")
        repo.create_deployment(session, project_id=p.id, status="running", image_tag="v1")
        _time.sleep(0.05)  # ensure distinct created_at timestamps
        repo.create_deployment(session, project_id=p.id, status="running", image_tag="v2")
        latest = repo.get_latest_deployment(session, p.id)
        assert latest is not None
        assert latest.image_tag == "v2"

    def test_get_latest_deployment_none(self, session: Session) -> None:
        p = repo.create_project(session, name="no-deploy-proj")
        assert repo.get_latest_deployment(session, p.id) is None

    def test_update_deployment(self, session: Session) -> None:
        p = repo.create_project(session, name="upd-deploy-proj")
        d = repo.create_deployment(session, project_id=p.id, status="pending")
        updated = repo.update_deployment(
            session, d, container_id="abc123", status="running"
        )
        assert updated.container_id == "abc123"
        assert updated.status == "running"
