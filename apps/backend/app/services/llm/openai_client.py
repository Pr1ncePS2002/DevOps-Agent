"""OpenAI-compatible LLM client using httpx (no openai SDK required)."""
from __future__ import annotations

import json

import httpx
import structlog

from app.common.settings import settings
from app.services.llm.base import BaseLLMClient

log = structlog.get_logger(__name__)

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class OpenAIClient(BaseLLMClient):
    """LLM client that speaks the OpenAI Chat Completions API.

    Works with any OpenAI-compatible endpoint (OpenAI, Azure, local proxies,
    Ollama in OpenAI-compat mode, etc.).
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Add it to your .env file to use the OpenAI provider."
            )
        self._api_key = settings.openai_api_key
        self._base_url = str(settings.openai_base_url).rstrip("/")
        self._model = settings.openai_model
        log.info("openai_client_initialised", model=self._model, base_url=self._base_url)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """Send a chat completion request and return the assistant message."""
        payload: dict = {
            "model": self._model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        log.debug(
            "openai_request",
            model=self._model,
            user_prompt_chars=len(user_prompt),
        )

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            )

        if response.status_code != 200:
            log.error(
                "openai_request_failed",
                status=response.status_code,
                body=response.text[:500],
            )
            response.raise_for_status()

        data = response.json()
        text: str = data["choices"][0]["message"]["content"]
        log.debug("openai_response", chars=len(text))
        return text

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> dict:
        """Use OpenAI's json_object response format for reliable JSON output."""
        payload: dict = {
            "model": self._model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        log.debug(
            "openai_json_request",
            model=self._model,
            user_prompt_chars=len(user_prompt),
        )

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            )

        if response.status_code != 200:
            log.error(
                "openai_json_request_failed",
                status=response.status_code,
                body=response.text[:500],
            )
            response.raise_for_status()

        data = response.json()
        raw: str = data["choices"][0]["message"]["content"]
        log.debug("openai_json_response", chars=len(raw))
        return json.loads(raw)
