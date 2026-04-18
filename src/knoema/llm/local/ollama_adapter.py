"""Ollama chat adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from knoema.llm.local.http import LocalLLMError, normalize_messages, numeric_option, post_json
from knoema.protocols import Message


class OllamaClient:
    """Client for Ollama's local `/api/chat` endpoint."""

    def __init__(
        self,
        *,
        model: str = "llama3.3",
        base_url: str = "http://localhost:11434",
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str:
        options: dict[str, int | float] = {}
        temperature = numeric_option(kwargs.get("temperature"))
        if temperature is not None:
            options["temperature"] = temperature
        max_tokens = numeric_option(kwargs.get("max_tokens"))
        if max_tokens is not None:
            options["num_predict"] = int(max_tokens)

        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": normalize_messages(messages),
            "stream": False,
        }
        if options:
            payload["options"] = options

        response = post_json(f"{self.base_url}/api/chat", payload, timeout=self.timeout)
        message = response.get("message")
        if not isinstance(message, dict):
            raise LocalLLMError("Ollama response did not include a message")
        content = message.get("content")
        if not isinstance(content, str):
            raise LocalLLMError("Ollama message content must be a string")
        return content


__all__ = ["OllamaClient"]
