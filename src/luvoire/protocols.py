"""Protocol definitions for Luvoire subsystems."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from luvoire.types import Memory

Message = Mapping[str, str]


@runtime_checkable
class PromptRenderable(Protocol):
    """Objects that can be rendered into an LLM system prompt."""

    def to_system_prompt(self) -> str: ...


@runtime_checkable
class MemoryWriter(Protocol):
    """Append-only write interface for memory stores."""

    def add(self, memory: Memory) -> None: ...


@runtime_checkable
class MemoryRetriever(Protocol):
    """Query interface for semantic or episodic memory stores."""

    def retrieve(self, query: str, k: int = 5, recency_bias: float = 0.3) -> Sequence[Memory]: ...


@runtime_checkable
class LLMClient(Protocol):
    """Provider-agnostic completion interface."""

    def complete(self, messages: Sequence[Message], **kwargs: Any) -> str: ...


__all__ = [
    "LLMClient",
    "MemoryRetriever",
    "MemoryWriter",
    "Message",
    "PromptRenderable",
]
