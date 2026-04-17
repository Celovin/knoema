"""Provider fallback gateway for LLM completions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

from knoema.protocols import LLMClient, Message


@dataclass(slots=True)
class LLMCallRecord:
    provider: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    elapsed_seconds: float
    success: bool
    error: str | None = None


class LLMGateway:
    """Try providers in order and keep lightweight usage records."""

    def __init__(self, providers: Sequence[tuple[str, LLMClient]]) -> None:
        if not providers:
            raise ValueError("providers must not be empty")
        self._providers = list(providers)
        self.records: list[LLMCallRecord] = []

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        prompt_tokens = estimate_tokens(_messages_to_text(messages))
        last_error: Exception | None = None
        for provider_name, provider in self._providers:
            started_at = perf_counter()
            try:
                response = provider.complete(messages, **kwargs)
            except Exception as exc:  # pragma: no cover - exact provider errors vary
                last_error = exc
                self.records.append(
                    LLMCallRecord(
                        provider=provider_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=0,
                        estimated_cost_usd=0.0,
                        elapsed_seconds=perf_counter() - started_at,
                        success=False,
                        error=str(exc),
                    )
                )
                continue

            completion_tokens = estimate_tokens(response)
            self.records.append(
                LLMCallRecord(
                    provider=provider_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    estimated_cost_usd=estimate_cost_usd(prompt_tokens, completion_tokens),
                    elapsed_seconds=perf_counter() - started_at,
                    success=True,
                )
            )
            return response

        raise RuntimeError("all LLM providers failed") from last_error


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return ((prompt_tokens * 0.003) + (completion_tokens * 0.015)) / 1000.0


def _messages_to_text(messages: Sequence[Message]) -> str:
    return "\n".join(message.get("content", "") for message in messages)


__all__ = ["LLMCallRecord", "LLMGateway", "estimate_cost_usd", "estimate_tokens"]
