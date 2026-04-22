"""llama.cpp server adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from knoema.llm.local.http import normalize_messages, numeric_option, openai_chat_content, post_json
from knoema.protocols import Message


class LlamaCppClient:
    """Client for llama.cpp's OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        *,
        model: str = "local-llama-cpp",
        base_url: str = "http://localhost:8080",
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": normalize_messages(messages),
            "stream": False,
        }
        temperature = numeric_option(kwargs.get("temperature"))
        if temperature is not None:
            payload["temperature"] = temperature
        max_tokens = numeric_option(kwargs.get("max_tokens"))
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)

        response = post_json(
            f"{self.base_url}/v1/chat/completions",
            payload,
            timeout=self.timeout,
        )
        return openai_chat_content(response)


__all__ = ["LlamaCppClient"]
