"""Wrapper around the Anthropic SDK with prompt caching and JSON-mode helpers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


class LLMError(RuntimeError):
    """Raised when the LLM call cannot produce a usable result."""


@dataclass
class StructuredResponse:
    text: str
    input_tokens: int
    output_tokens: int


class ClaudeClient:
    """Thin wrapper exposing `complete` (text) and `complete_json` (structured).

    The first call sends the `system` prompt with cache_control=ephemeral so subsequent
    calls within the 5-minute cache window hit cache. Caller controls the system
    content; this class adds no game-specific knowledge.
    """

    def __init__(
        self,
        sdk: Any | None = None,
        model: str = DEFAULT_MODEL,
        max_json_retries: int = 2,
        max_tokens: int = 800,
    ):
        if sdk is None:
            import anthropic  # imported lazily so tests don't need API key

            sdk = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self._sdk = sdk
        self._model = model
        self._max_json_retries = max_json_retries
        self._max_tokens = max_tokens

    def complete(self, *, system: str, user: str) -> StructuredResponse:
        system_blocks = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        msg = self._sdk.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_blocks,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text if msg.content else ""
        in_tok = getattr(msg.usage, "input_tokens", 0) if getattr(msg, "usage", None) else 0
        out_tok = getattr(msg.usage, "output_tokens", 0) if getattr(msg, "usage", None) else 0
        return StructuredResponse(text=text, input_tokens=in_tok, output_tokens=out_tok)

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        last_text = ""
        for _ in range(self._max_json_retries):
            resp = self.complete(system=system, user=user)
            last_text = resp.text
            parsed = self._try_parse(last_text)
            if parsed is not None:
                return parsed
        raise LLMError(
            f"could not parse JSON response after {self._max_json_retries} attempts: {last_text!r}"
        )

    @staticmethod
    def _try_parse(text: str) -> dict[str, Any] | None:
        candidates = [text.strip()]
        for m in _JSON_FENCE_RE.finditer(text):
            candidates.append(m.group(1))
        for c in candidates:
            try:
                obj = json.loads(c)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
        return None
