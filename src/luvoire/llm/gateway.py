"""Provider fallback gateway for LLM completions."""

from __future__ import annotations

import json
import re
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
from luvoire.observability.tracing import genai_attributes, trace_span
from luvoire.protocols import LLMClient, Message

# Regex patterns for credential strings that may surface inside provider
# exception messages (auth failure, billing errors). Matched substrings
# are replaced with ``***`` before the error string is stored in
# :class:`LLMCallRecord.error`. Adding a new provider key format means
# adding it here AND covering the case in ``test_llm_gateway_redaction``.
_SECRET_REDACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),  # OpenAI / Anthropic / generic sk-* keys
    re.compile(r"sk_(?:test|live)_[A-Za-z0-9]{16,}"),  # Stripe-style
    re.compile(r"luvoire_ak[a-f0-9]+_[A-Za-z0-9_\-]{16,}"),  # Luvoire tenant tokens
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]{16,}", re.IGNORECASE),  # bearer headers
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{8,}"),  # Slack tokens (defence-in-depth)
)


def _redact_secrets(message: str) -> str:
    """Replace credential-looking substrings with ``***``.

    Provider SDKs sometimes include the offending API key inside
    ``AuthenticationError``-style messages. Those exceptions reach
    :class:`LLMCallRecord.error` as ``str(exc)``, which can be exported
    to logs / traces / metrics. We scrub before storage so a downstream
    log shipper cannot re-emit a live key. Round-5 audit hardening.
    """

    redacted = message
    for pattern in _SECRET_REDACTION_PATTERNS:
        redacted = pattern.sub("***", redacted)
    return redacted


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


_DEFAULT_FALLBACK_DEADLINE_SECONDS: float = 120.0
"""Default cumulative deadline across the provider fallback loop.

Each individual provider already enforces its own per-call timeout (via
``httpx`` defaults inside the SDK), but if every provider in the chain
hangs at its own timeout the caller-visible wait is the **sum** of those
timeouts. This deadline bounds that sum so a misconfigured cluster of
slow providers cannot turn a single ``complete()`` call into a 10-minute
hang on the request-handling thread. 120s leaves headroom for the
typical Anthropic/OpenAI tail latency on a long-context completion.
"""


class LLMGateway:
    """Try providers in order and keep lightweight usage records."""

    def __init__(
        self,
        providers: Sequence[tuple[str, LLMClient]],
        *,
        replay_cache: ReplayCache | None = None,
        fallback_deadline_seconds: float = _DEFAULT_FALLBACK_DEADLINE_SECONDS,
    ) -> None:
        if not providers:
            raise ValueError("providers must not be empty")
        if fallback_deadline_seconds <= 0:
            raise ValueError("fallback_deadline_seconds must be positive")
        self._providers = list(providers)
        self._replay_cache = replay_cache if replay_cache is not None else replay_cache_from_env()
        self._fallback_deadline_seconds = float(fallback_deadline_seconds)
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
        deadline = perf_counter() + self._fallback_deadline_seconds
        for provider_name, provider in self._providers:
            if perf_counter() >= deadline:
                raise TimeoutError(
                    "LLMGateway provider fallback exceeded "
                    f"{self._fallback_deadline_seconds:.1f}s deadline; "
                    "remaining providers skipped to bound caller wait"
                ) from last_error
            started_at = perf_counter()
            model = _provider_model(provider_name, provider)
            with trace_span(
                "luvoire.llm.provider.complete",
                genai_attributes(
                    system=provider_name,
                    operation="complete",
                    model=model,
                    temperature=_float_kwarg(kwargs, "temperature"),
                    max_tokens=_int_kwarg(kwargs, "max_tokens"),
                ),
            ) as span:
                try:
                    response = provider.complete(messages, **dict(kwargs))
                except Exception as exc:  # pragma: no cover - exact provider errors vary
                    last_error = exc
                    elapsed = perf_counter() - started_at
                    if span is not None:
                        span.set_attribute("luvoire.llm.success", False)
                        span.set_attribute("error.type", type(exc).__name__)
                    self.records.append(
                        LLMCallRecord(
                            provider=provider_name,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=0,
                            estimated_cost_usd=0.0,
                            elapsed_seconds=elapsed,
                            success=False,
                            error=_redact_secrets(str(exc)),
                        )
                    )
                    continue

                completion_tokens = estimate_tokens(response)
                elapsed = perf_counter() - started_at
                if span is not None:
                    span.set_attribute("luvoire.llm.success", True)
                    span.set_attribute("gen_ai.usage.input_tokens", prompt_tokens)
                    span.set_attribute("gen_ai.usage.output_tokens", completion_tokens)
                self.records.append(
                    LLMCallRecord(
                        provider=provider_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        estimated_cost_usd=estimate_cost_usd(prompt_tokens, completion_tokens),
                        elapsed_seconds=elapsed,
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
        deadline = perf_counter() + self._fallback_deadline_seconds
        for provider_name, provider in self._providers:
            if perf_counter() >= deadline:
                raise TimeoutError(
                    "LLMGateway provider fallback exceeded "
                    f"{self._fallback_deadline_seconds:.1f}s deadline; "
                    "remaining replay-cache providers skipped"
                ) from last_error
            model = _provider_model(provider_name, provider)
            cache_key = self._replay_cache.key(
                model=model,
                prompt=prompt,
                sampling=sampling,
                seed=seed,
            )
            started_at = perf_counter()
            with trace_span(
                "luvoire.llm.provider.complete",
                {
                    **genai_attributes(
                        system=provider_name,
                        operation="replay_cache",
                        model=model,
                        temperature=_float_kwarg(kwargs, "temperature"),
                        max_tokens=_int_kwarg(kwargs, "max_tokens"),
                    ),
                    "luvoire.replay_cache.enabled": True,
                },
            ) as span:
                try:
                    recorded = self._replay_cache.get(cache_key)
                except ReplayCacheMiss:
                    elapsed = perf_counter() - started_at
                    if span is not None:
                        span.set_attribute("luvoire.replay_cache.hit", False)
                        span.set_attribute("luvoire.llm.success", False)
                    self.records.append(
                        LLMCallRecord(
                            provider=provider_name,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=0,
                            estimated_cost_usd=0.0,
                            elapsed_seconds=elapsed,
                            success=False,
                            error=f"replay cache miss for {provider_name}",
                        )
                    )
                    raise
                if recorded is not None:
                    elapsed = perf_counter() - started_at
                    if span is not None:
                        span.set_attribute("luvoire.replay_cache.hit", True)
                        span.set_attribute("luvoire.llm.success", True)
                        span.set_attribute("gen_ai.usage.input_tokens", recorded.prompt_tokens)
                        span.set_attribute("gen_ai.usage.output_tokens", recorded.completion_tokens)
                    self.records.append(
                        LLMCallRecord(
                            provider=provider_name,
                            prompt_tokens=recorded.prompt_tokens,
                            completion_tokens=recorded.completion_tokens,
                            estimated_cost_usd=0.0,
                            elapsed_seconds=elapsed,
                            success=True,
                        )
                    )
                    return recorded.text

                try:
                    response = provider.complete(messages, **dict(kwargs))
                except Exception as exc:  # pragma: no cover - exact provider errors vary
                    last_error = exc
                    elapsed = perf_counter() - started_at
                    if span is not None:
                        span.set_attribute("luvoire.replay_cache.hit", False)
                        span.set_attribute("luvoire.llm.success", False)
                        span.set_attribute("error.type", type(exc).__name__)
                    self.records.append(
                        LLMCallRecord(
                            provider=provider_name,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=0,
                            estimated_cost_usd=0.0,
                            elapsed_seconds=elapsed,
                            success=False,
                            error=_redact_secrets(str(exc)),
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
                elapsed = perf_counter() - started_at
                if span is not None:
                    span.set_attribute("luvoire.replay_cache.hit", False)
                    span.set_attribute("luvoire.llm.success", True)
                    span.set_attribute("gen_ai.usage.input_tokens", prompt_tokens)
                    span.set_attribute("gen_ai.usage.output_tokens", completion_tokens)
                self.records.append(
                    LLMCallRecord(
                        provider=provider_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        estimated_cost_usd=estimate_cost_usd(prompt_tokens, completion_tokens),
                        elapsed_seconds=elapsed,
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


_TIKTOKEN_ENCODING_NAME = "cl100k_base"
"""Default ``tiktoken`` encoding (used by GPT-4 / Claude 3+ via litellm).

We only consult tiktoken when it is actually installed; otherwise we
fall back to the historical ``len(text) // 4`` heuristic so air-gapped
environments and minimal-deps installs keep working. The encoding name
is locked here rather than per-model because Luvoire's billing meter
treats prompt tokens as a coarse estimate at the floor — the exact
tokenizer used by Anthropic / OpenAI for billing is privileged and not
publicly auditable, so a single ``cl100k_base`` measurement gives
better fidelity than ``len/4`` without claiming exact agreement.
"""

_tiktoken_encoder: object | None = None
_tiktoken_attempted: bool = False


def _get_tiktoken_encoder() -> object | None:
    """Lazy-load the tiktoken encoder; cache the result (or ``None``).

    Returns the encoder on success, ``None`` if tiktoken is not
    installed or the encoding could not be resolved. The result is
    cached after the first attempt so repeated ``estimate_tokens``
    calls do not pay the import cost.
    """

    global _tiktoken_encoder, _tiktoken_attempted
    if _tiktoken_attempted:
        return _tiktoken_encoder
    _tiktoken_attempted = True
    try:
        import tiktoken  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    try:
        _tiktoken_encoder = tiktoken.get_encoding(_TIKTOKEN_ENCODING_NAME)
    except Exception:
        # Pinned encoding not available (e.g. tiktoken_ext data missing
        # in a minimal install); silently fall back to the heuristic.
        _tiktoken_encoder = None
    return _tiktoken_encoder


def estimate_tokens(text: str) -> int:
    """Estimate token count for ``text``.

    Uses ``tiktoken`` (``cl100k_base``) when available so the meter
    floor reflects realistic token counts on Latin / mixed-script
    Korean text — the legacy ``len(text) // 4`` heuristic over-counts
    Hangul and under-counts code-heavy prompts. Falls back to the
    heuristic when tiktoken is not installed so the billing layer
    keeps working in air-gapped CI / minimal deployments.
    """

    if not text:
        return 0
    encoder = _get_tiktoken_encoder()
    if encoder is not None:
        try:
            return max(1, len(encoder.encode(text)))  # type: ignore[attr-defined]
        except Exception:
            # Defence-in-depth: any tokenizer error falls back to the
            # heuristic so a corrupt encoder cannot wedge the meter.
            pass
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


def _float_kwarg(kwargs: Mapping[str, object], key: str) -> float | None:
    value = kwargs.get(key)
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_kwarg(kwargs: Mapping[str, object], key: str) -> int | None:
    value = kwargs.get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


__all__ = [
    "CachedLLMClient",
    "LLMCacheStats",
    "LLMCallRecord",
    "LLMGateway",
    "estimate_cost_usd",
    "estimate_tokens",
]
