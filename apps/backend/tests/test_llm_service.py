"""Tests for the LLM service abstraction layer."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMFactory:

    def test_factory_returns_gemini_client(self) -> None:
        """Factory should return GeminiClient when LLM_PROVIDER=GEMINI."""
        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = "GEMINI"
            mock_settings.gemini_api_key = "test-key"
            mock_settings.gemini_model = "gemini-2.5-pro"

            from app.services.llm.factory import get_llm_client
            from app.services.llm.gemini_client import GeminiClient

            client = get_llm_client()
            assert isinstance(client, GeminiClient)

    def test_factory_returns_openai_client(self) -> None:
        """Factory should return OpenAIClient when LLM_PROVIDER=OPENAI."""
        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = "OPENAI"
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_base_url = "https://api.openai.com/v1"
            mock_settings.openai_model = "gpt-4"

            from app.services.llm.factory import get_llm_client
            from app.services.llm.openai_client import OpenAIClient

            client = get_llm_client()
            assert isinstance(client, OpenAIClient)

    def test_factory_raises_on_unknown_provider(self) -> None:
        """Factory should raise ValueError for unknown provider."""
        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = "INVALID_PROVIDER"

            from app.services.llm.factory import get_llm_client

            with pytest.raises(ValueError, match="Unknown LLM provider"):
                get_llm_client()


class TestSummaryGenerator:

    @pytest.mark.asyncio
    async def test_generate_summary_safe_returns_none_on_failure(self) -> None:
        """Safe wrapper should return None when execution is not found."""
        from sqlmodel import SQLModel, Session, create_engine

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            from app.services.summary_generator import generate_deployment_summary_safe
            result = await generate_deployment_summary_safe(99999, session)
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_summary_calls_llm(self) -> None:
        """Summary generator should call the LLM client with execution data."""
        from sqlmodel import SQLModel, Session, create_engine
        from app.persistence import repositories as repo
        from datetime import datetime, timezone

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(engine)

        with Session(engine, expire_on_commit=False) as session:
            p = repo.create_project(session, name="test-proj")
            plan = repo.create_plan(
                session, project_id=p.id, raw_command="deploy",
                action="deploy", version="1.0", environments=["staging"],
                post_steps=[], warnings=[],
            )
            ex = repo.create_execution(session, plan.id)
            repo.set_execution_status(session, ex, "running")
            repo.append_execution_log(session, ex, "Build succeeded")
            repo.set_execution_status(session, ex, "succeeded")

            mock_response = {
                "summary": "Test deploy succeeded",
                "key_events": ["Build succeeded"],
                "root_cause": None,
                "recommendations": ["Add tests"],
                "severity": "info",
            }

            mock_client = AsyncMock()
            mock_client.complete_json = AsyncMock(return_value=mock_response)

            with patch("app.services.summary_generator.get_llm_client", return_value=mock_client):
                from app.services.summary_generator import generate_deployment_summary
                result = await generate_deployment_summary(ex.id, session)

            assert result["summary"] == "Test deploy succeeded"
            assert result["severity"] == "info"
            mock_client.complete_json.assert_called_once()
