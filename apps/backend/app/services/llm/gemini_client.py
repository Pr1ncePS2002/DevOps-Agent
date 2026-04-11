"""Gemini LLM client using the google-generativeai SDK."""
from __future__ import annotations

import structlog

from app.common.settings import settings
from app.services.llm.base import BaseLLMClient

log = structlog.get_logger(__name__)


class GeminiClient(BaseLLMClient):
    """LLM client backed by Google Gemini."""

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file to use the Gemini provider."
            )
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install 'google-generativeai>=0.8.0'"
            ) from exc

        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai
        self._model_name = settings.gemini_model
        log.info("gemini_client_initialised", model=self._model_name)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """Send a prompt to Gemini and return the text response."""
        import asyncio

        generation_config = self._genai.GenerationConfig(temperature=temperature)

        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=generation_config,
        )

        log.debug(
            "gemini_request",
            model=self._model_name,
            user_prompt_chars=len(user_prompt),
        )

        # The google-generativeai SDK is synchronous; run in a thread pool so
        # we don't block the asyncio event loop.
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_prompt),
        )

        text: str = response.text
        log.debug("gemini_response", chars=len(text))
        return text
