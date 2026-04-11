"""LLM client factory — returns the correct client based on configuration."""
from __future__ import annotations

import structlog

from app.common.settings import settings
from app.services.llm.base import BaseLLMClient

log = structlog.get_logger(__name__)

_SUPPORTED_PROVIDERS = {"GEMINI", "OPENAI", "OLLAMA"}


def get_llm_client() -> BaseLLMClient:
    """Return an initialised :class:`BaseLLMClient` for the configured provider.

    The provider is controlled by the ``LLM_PROVIDER`` environment variable
    (mapped to ``settings.llm_provider``).  Accepted values:

    * ``GEMINI``  — Google Gemini via ``google-generativeai`` SDK
    * ``OPENAI``  — OpenAI-compatible API via ``httpx``
    * ``OLLAMA``  — Ollama local models (uses the OpenAI-compatible endpoint)

    Raises :class:`ValueError` if the provider is unknown or the required API
    key is missing.
    """
    provider = (settings.llm_provider or "OPENAI").upper()
    log.info("llm_factory_resolving", provider=provider)

    if provider == "GEMINI":
        from app.services.llm.gemini_client import GeminiClient

        return GeminiClient()

    if provider == "OPENAI":
        from app.services.llm.openai_client import OpenAIClient

        return OpenAIClient()

    if provider == "OLLAMA":
        # Reuse the OpenAI-compatible client, but point it at the Ollama base
        # URL and the configured Ollama model.
        from app.services.llm.openai_client import OpenAIClient
        from app.common import settings as _settings_mod

        # Temporarily patch settings so OpenAIClient picks up Ollama values.
        # We do this without mutating the global singleton to keep it
        # thread-safe — we just construct the client with a small shim.
        class _OllamaSettings:
            openai_api_key: str = "ollama"  # Ollama doesn't need a real key
            openai_base_url: str = str(settings.ollama_base_url).rstrip("/")
            openai_model: str = settings.ollama_model

        # Build the client by monkey-patching at the module level is fragile;
        # instead instantiate OpenAIClient and override its private attrs.
        client = object.__new__(OpenAIClient)
        client._api_key = "ollama"
        client._base_url = str(settings.ollama_base_url).rstrip("/")
        client._model = settings.ollama_model
        log.info(
            "ollama_client_initialised",
            base_url=client._base_url,
            model=client._model,
        )
        return client  # type: ignore[return-value]

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        f"Supported values: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
    )
