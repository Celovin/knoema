"""Local deterministic fallback client."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from luvoire.protocols import Message


class LocalClient:
    """Callable-backed local client, useful for tests and offline demos."""

    def __init__(self, responder: Callable[[Sequence[Message]], str] | None = None) -> None:
        self._responder = responder or _default_responder

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        return self._responder(messages)


def _default_responder(messages: Sequence[Message]) -> str:
    last_user_message = next(
        (message.get("content", "") for message in reversed(messages) if message.get("role") == "user"),
        "",
    )
    return last_user_message[:500] or "No local response available."


__all__ = ["LocalClient"]
