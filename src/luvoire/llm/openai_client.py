"""OpenAI SDK adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from luvoire.protocols import Message


class OpenAIClient:
    """Thin OpenAI Responses API wrapper."""

    def __init__(self, *, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str:
        from openai import OpenAI

        client: Any = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": message.get("role", "user"), "content": message.get("content", "")}
                for message in messages
            ],
            temperature=float(kwargs.get("temperature", 0.7)),
            max_output_tokens=int(kwargs.get("max_tokens", 1024)),
        )
        return str(response.output_text).strip()


__all__ = ["OpenAIClient"]
