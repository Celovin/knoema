"""Provider fallback gateway for LLM completions."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from threading import Event, Lock
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


@dataclass(frozen=True, slots=True)
class LLMCacheStats:
    hits: int
    misses: int
    entries: int

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return self.hits / self.requests


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


class CachedLLMClient:
    """Thread-safe in-memory cache for identical LLM prompts."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client
        self._cache: dict[str, str] = {}
        self._inflight: dict[str, _PendingCall] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        cache_key = _cache_key(messages, kwargs)
        is_leader = False
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._hits += 1
                return cached
            pending = self._inflight.get(cache_key)
            if pending is None:
                pending = _PendingCall()
                self._inflight[cache_key] = pending
                self._misses += 1
                is_leader = True
            else:
                self._hits += 1

        if is_leader:
            try:
                response = self._client.complete(messages, **kwargs)
            except Exception as exc:
                with self._lock:
                    pending.error = exc
                    pending.event.set()
                    self._inflight.pop(cache_key, None)
                raise
            with self._lock:
                self._cache[cache_key] = response
                pending.response = response
                pending.event.set()
                self._inflight.pop(cache_key, None)
            return response

        pending.event.wait()
        if pending.error is not None:
            raise pending.error
        if pending.response is None:
            raise RuntimeError("cached LLM request completed without a response")
        return pending.response

    def cache_stats(self) -> LLMCacheStats:
        with self._lock:
            return LLMCacheStats(
                hits=self._hits,
                misses=self._misses,
                entries=len(self._cache),
            )


@dataclass(slots=True)
class _PendingCall:
    event: Event = field(default_factory=Event)
    response: str | None = None
    error: Exception | None = None


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return ((prompt_tokens * 0.003) + (completion_tokens * 0.015)) / 1000.0


def _messages_to_text(messages: Sequence[Message]) -> str:
    return "\n".join(message.get("content", "") for message in messages)


def _cache_key(messages: Sequence[Message], kwargs: Mapping[str, object]) -> str:
    payload = {
        "messages": [
            {
                "role": message.get("role", ""),
                "content": message.get("content", ""),
            }
            for message in messages
        ],
        "kwargs": sorted(kwargs.items()),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "CachedLLMClient",
    "LLMCacheStats",
    "LLMCallRecord",
    "LLMGateway",
    "estimate_cost_usd",
    "estimate_tokens",
]
