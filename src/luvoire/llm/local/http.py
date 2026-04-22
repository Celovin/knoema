"""Shared HTTP helpers for local LLM server adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib import error, request

from luvoire.protocols import Message


class LocalLLMError(RuntimeError):
    """Raised when a local LLM server returns an unusable response."""


def normalize_messages(messages: Sequence[Message]) -> list[dict[str, str]]:
    return [
        {
            "role": message.get("role", "user"),
            "content": message.get("content", ""),
        }
        for message in messages
    ]


def post_json(
    url: str,
    payload: Mapping[str, Any],
    *,
    timeout: float,
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    encoded = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    http_request = request.Request(url, data=encoded, headers=request_headers, method="POST")
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:  # pragma: no cover - server availability varies
        raise LocalLLMError(f"local LLM request failed: {exc}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LocalLLMError("local LLM response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise LocalLLMError("local LLM response must be a JSON object")
    return parsed


def openai_chat_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LocalLLMError("OpenAI-compatible response did not include choices")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise LocalLLMError("OpenAI-compatible choice must be an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise LocalLLMError("OpenAI-compatible choice did not include a message")
    content = message.get("content")
    if not isinstance(content, str):
        raise LocalLLMError("OpenAI-compatible message content must be a string")
    return content


def numeric_option(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


__all__ = ["LocalLLMError", "normalize_messages", "numeric_option", "openai_chat_content", "post_json"]
