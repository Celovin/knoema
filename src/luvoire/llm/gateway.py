"""Provider fallback gateway for LLM completions."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from threading import Event, Lock
from time import perf_counter

from luvoire.core.replay_cache import (
    RecordedResponse,
    ReplayCache,
    ReplayCacheMiss,
    replay_cache_from_env,
)
from luvoire.protocols import LLMClient, Message


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

    def __init__(
        self,
        providers: Sequence[tuple[str, LLMClient]],
        *,
        replay_cache: ReplayCache | None = None,
    ) -> None:
        if not providers:
            raise ValueError("providers must not be empty")
        self._providers = list(providers)
        self._replay_cache = replay_cache if replay_cache is not None else replay_cache_from_env()
        self.records: list[LLMCallRecord] = []

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        prompt_tokens = estimate_tokens(_messages_to_text(messages))
        if self._replay_cache is not None:
            return self._complete_with_replay_cache(messages, kwargs, prompt_tokens)
        return self._complete_live(messages, kwargs, prompt_tokens)

    def _complete_live(
        self,
        messages: Sequence[Message],
        kwargs: Mapping[str, object],
        prompt_tokens: int,
    ) -> str:
        last_error: Exception | None = None
        for provider_name, provider in self._providers:
            started_at = perf_counter()
            try:
                response = provider.complete(messages, **dict(kwargs))
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

    def _complete_with_replay_cache(
        self,
        messages: Sequence[Message],
        kwargs: Mapping[str, object],
        prompt_tokens: int,
    ) -> str:
        if self._replay_cache is None:
            raise RuntimeError("replay cache helper called without an active cache")
        last_error: Exception | None = None
        prompt = _messages_to_prompt(messages)
        seed = _seed_from_kwargs(kwargs)
        sampling = _sampling_from_kwargs(kwargs)
        for provider_name, provider in self._providers:
            model = _provider_model(provider_name, provider)
            cache_key = self._replay_cache.key(
                model=model,
                prompt=prompt,
                sampling=sampling,
                seed=seed,
            )
            started_at = perf_counter()
            try:
                recorded = self._replay_cache.get(cache_key)
            except ReplayCacheMiss:
                self.records.append(
                    LLMCallRecord(
                        provider=provider_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=0,
                        estimated_cost_usd=0.0,
                        elapsed_seconds=perf_counter() - started_at,
                        success=False,
                        error=f"replay cache miss for {provider_name}",
                    )
                )
                raise
            if recorded is not None:
                self.records.append(
                    LLMCallRecord(
                        provider=provider_name,
                        prompt_tokens=recorded.prompt_tokens,
                        completion_tokens=recorded.completion_tokens,
                        estimated_cost_usd=0.0,
                        elapsed_seconds=perf_counter() - started_at,
                        success=True,
                    )
                )
                return recorded.text

            try:
                response = provider.complete(messages, **dict(kwargs))
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
            self._replay_cache.put(
                cache_key,
                RecordedResponse(
                    text=response,
                    finish_reason=str(kwargs.get("finish_reason", "stop")),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model_fingerprint=_model_fingerprint(provider),
                    captured_at=datetime.now(UTC),
                ),
            )
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


def _messages_to_prompt(messages: Sequence[Message]) -> str:
    payload = [
        {
            "role": message.get("role", ""),
            "content": message.get("content", ""),
        }
        for message in messages
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _seed_from_kwargs(kwargs: Mapping[str, object]) -> int:
    seed = kwargs.get("seed", 0)
    if seed is None:
        return 0
    if isinstance(seed, int):
        return seed
    if isinstance(seed, float):
        return int(seed)
    if isinstance(seed, str):
        return int(seed)
    return int(str(seed))


def _sampling_from_kwargs(kwargs: Mapping[str, object]) -> dict[str, object]:
    return {str(key): value for key, value in kwargs.items() if key != "seed"}


def _provider_model(provider_name: str, provider: LLMClient) -> str:
    model = getattr(provider, "model", None)
    return str(model) if model else provider_name


def _model_fingerprint(provider: LLMClient) -> str | None:
    fingerprint = getattr(provider, "model_fingerprint", None)
    return str(fingerprint) if fingerprint else None


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
