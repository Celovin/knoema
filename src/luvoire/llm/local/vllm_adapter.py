"""vLLM OpenAI-compatible server adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from luvoire.llm.local.http import normalize_messages, numeric_option, openai_chat_content, post_json
from luvoire.protocols import Message


class VLLMClient:
    """Client for vLLM's OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        *,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
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

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        response = post_json(
            f"{self.base_url}/v1/chat/completions",
            payload,
            timeout=self.timeout,
            headers=headers,
        )
        return openai_chat_content(response)


__all__ = ["VLLMClient"]
