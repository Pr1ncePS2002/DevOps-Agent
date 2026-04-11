"""LLM service abstraction layer.

Usage::

    from app.services.llm import get_llm_client, BaseLLMClient

    client: BaseLLMClient = get_llm_client()
    text = await client.complete(system_prompt, user_prompt)
    data = await client.complete_json(system_prompt, user_prompt)
"""
from __future__ import annotations

from app.services.llm.base import BaseLLMClient
from app.services.llm.factory import get_llm_client

__all__ = ["BaseLLMClient", "get_llm_client"]
