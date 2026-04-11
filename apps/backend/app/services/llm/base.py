"""Abstract base class for all LLM provider clients."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Provider-agnostic LLM client interface."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """Send a completion request and return the raw text response."""
        ...

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> dict:
        """Send a completion request and parse the response as JSON.

        Retries once if the initial parse fails, instructing the model to
        return only valid JSON.  Also handles the common case where the model
        wraps its response in a markdown code-fence (```json … ```).
        """
        raw = await self.complete(system_prompt, user_prompt, temperature=0.0)
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            return parsed

        # --- Retry: tell the model to return raw JSON only ---
        retry_user = (
            f"{user_prompt}\n\n"
            "IMPORTANT: Your previous response could not be parsed as JSON. "
            "Return ONLY valid JSON with no additional text or markdown fences."
        )
        raw2 = await self.complete(system_prompt, retry_user, temperature=0.0)
        parsed2 = self._try_parse_json(raw2)
        if parsed2 is not None:
            return parsed2

        raise ValueError(
            f"LLM did not return valid JSON after retry.\nRaw response: {raw2!r}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        """Attempt to extract and parse JSON from *text*.

        Handles:
        1. Plain JSON strings.
        2. JSON wrapped in markdown code fences (```json … ``` or ``` … ```).
        """
        text = text.strip()

        # Try direct parse first (fastest path)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strip markdown fences and try again
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except json.JSONDecodeError:
                pass

        # Last resort: find the first {...} block in the response
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                pass

        return None
