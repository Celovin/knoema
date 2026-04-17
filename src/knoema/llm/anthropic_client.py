"""Anthropic SDK adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from knoema.protocols import Message


class AnthropicClient:
    """Thin Anthropic Messages API wrapper."""

    def __init__(self, *, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str:
        from anthropic import Anthropic

        client: Any = Anthropic(api_key=self.api_key)
        system_message, user_messages = _split_system_message(messages)
        response = client.messages.create(
            model=self.model,
            max_tokens=int(kwargs.get("max_tokens", 1024)),
            temperature=float(kwargs.get("temperature", 0.7)),
            system=system_message,
            messages=[
                {
                    "role": "assistant" if message.get("role") == "assistant" else "user",
                    "content": message.get("content", ""),
                }
                for message in user_messages
            ],
        )
        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(str(getattr(block, "text", "")))
        return "\n".join(text_parts).strip()


def _split_system_message(messages: Sequence[Message]) -> tuple[str, list[Message]]:
    system_parts: list[str] = []
    user_messages: list[Message] = []
    for message in messages:
        if message.get("role") == "system":
            system_parts.append(message.get("content", ""))
        else:
            user_messages.append(message)
    return "\n".join(system_parts), user_messages


__all__ = ["AnthropicClient"]
