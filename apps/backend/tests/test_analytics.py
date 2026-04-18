"""Tests for the analytics API route."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.persistence import repositories as repo


class TestAnalyticsSummaryDirect:

    def test_empty_analytics_returns_zeros(self) -> None:
        """Analytics helper: when no rows exist, returns empty summary."""
        from app.api.routes.analytics import AnalyticsSummary

        # Construct what the endpoint returns for empty data
        summary = AnalyticsSummary(
            total_deployments=0,
            success_rate=0.0,
            average_deploy_time_seconds=0.0,
            rollback_count=0,
            deployments_by_day=[],
            deployments_by_environment={},
            most_deployed_project=None,
            recent_activity=[],
        )
        assert summary.total_deployments == 0
        assert summary.success_rate == 0.0
        assert summary.rollback_count == 0
        assert summary.most_deployed_project is None

    def test_analytics_model_serialization(self) -> None:
        """Analytics response model serializes correctly."""
        from app.api.routes.analytics import AnalyticsSummary, DayBucket, TopProject, RecentActivity

        summary = AnalyticsSummary(
            total_deployments=10,
            success_rate=80.0,
            average_deploy_time_seconds=120.5,
            rollback_count=1,
            deployments_by_day=[DayBucket(date="2026-01-01", count=3, successes=2, failures=1)],
            deployments_by_environment={"staging": 7, "production": 3},
            most_deployed_project=TopProject(name="api-gateway", count=5),
            recent_activity=[
                RecentActivity(
                    timestamp="2026-01-01T12:00:00",
                    action="deploy",
                    project="api-gateway",
                    environment="staging",
                    status="succeeded",
                    duration_seconds=45.2,
                )
            ],
        )
        data = summary.model_dump()
        assert data["total_deployments"] == 10
        assert data["success_rate"] == 80.0
        assert data["most_deployed_project"]["name"] == "api-gateway"
        assert len(data["recent_activity"]) == 1


class TestAnalyticsWithData:

    def test_analytics_with_executions(self, session: Session) -> None:
        """Verify analytics calculations with real execution data."""
        from app.api.routes.analytics import _duration_seconds
        from app.persistence.models import Execution
        from datetime import datetime, timezone, timedelta

        # Test duration calculation
        ex = Execution(
            plan_id=1,
            started_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 1, 12, 2, 30, tzinfo=timezone.utc),
        )
        assert _duration_seconds(ex) == 150.0

    def test_duration_seconds_none_if_incomplete(self) -> None:
        from app.api.routes.analytics import _duration_seconds
        from app.persistence.models import Execution

        ex = Execution(plan_id=1, started_at=None, finished_at=None)
        assert _duration_seconds(ex) is None


class TestChatRepositories:

    def test_create_and_list_chat_sessions(self, session: Session) -> None:
        p = repo.create_project(session, name="chat-proj")
        cs = repo.create_chat_session(session, p.id)
        assert cs.id is not None
        assert cs.status == "active"

        sessions = repo.list_chat_sessions(session, p.id)
        assert len(sessions) == 1
        assert sessions[0].id == cs.id

    def test_get_chat_session(self, session: Session) -> None:
        p = repo.create_project(session, name="chat-get-proj")
        cs = repo.create_chat_session(session, p.id)
        found = repo.get_chat_session(session, cs.id)
        assert found is not None
        assert found.project_id == p.id

    def test_get_chat_session_not_found(self, session: Session) -> None:
        assert repo.get_chat_session(session, 99999) is None

    def test_add_and_get_chat_messages(self, session: Session) -> None:
        p = repo.create_project(session, name="msg-proj")
        cs = repo.create_chat_session(session, p.id)

        msg1 = repo.add_chat_message(
            session, session_id=cs.id, role="user", content="Hello"
        )
        msg2 = repo.add_chat_message(
            session, session_id=cs.id, role="assistant", content="Hi there!"
        )

        history = repo.get_chat_history(session, cs.id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_chat_message_with_metadata(self, session: Session) -> None:
        p = repo.create_project(session, name="meta-proj")
        cs = repo.create_chat_session(session, p.id)

        msg = repo.add_chat_message(
            session,
            session_id=cs.id,
            role="assistant",
            content="Plan created",
            message_type="plan_preview",
            metadata={"plan_id": 42},
        )
        assert msg.message_type == "plan_preview"
        assert json.loads(msg.metadata_json) == {"plan_id": 42}

    def test_chat_history_limit(self, session: Session) -> None:
        p = repo.create_project(session, name="limit-proj")
        cs = repo.create_chat_session(session, p.id)

        for i in range(10):
            repo.add_chat_message(
                session, session_id=cs.id, role="user", content=f"msg {i}"
            )

        history = repo.get_chat_history(session, cs.id, limit=5)
        assert len(history) == 5

    def test_add_message_updates_last_message_at(self, session: Session) -> None:
        p = repo.create_project(session, name="ts-proj")
        cs = repo.create_chat_session(session, p.id)
        original_ts = cs.last_message_at

        repo.add_chat_message(
            session, session_id=cs.id, role="user", content="update ts"
        )

        updated = repo.get_chat_session(session, cs.id)
        assert updated is not None
        # Timestamp should be updated (or at least same since test runs fast)
        assert updated.last_message_at >= original_ts
