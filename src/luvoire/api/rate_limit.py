"""Simple token-bucket rate limiting for the Luvoire API server."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, Request, WebSocket, WebSocketException, status

from luvoire.config import get_env


@dataclass(slots=True)
class TokenBucket:
    tokens: float
    last_refill: float


class RateLimitBackend(Protocol):
    """Protocol implemented by both in-memory and Redis backends.

    Backends MUST be safe to call from multiple threads. The Redis
    backend is the only way to get bucket state that survives a
    process restart and is shared across replicas — without it, a
    multi-replica deploy effectively multiplies every tenant's quota
    by the replica count.
    """

    def consume(self, key: str, *, cost: float, tokens_per_second: float, burst: float) -> bool:  # pragma: no cover
        ...


class _InMemoryBackend:
    """Default backend — single-process token bucket.

    Bucket state lives in ``self._buckets`` and is lost on restart. Use
    ``RedisRateLimitBackend`` in production multi-replica deployments.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def consume(self, key: str, *, cost: float, tokens_per_second: float, burst: float) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(tokens=burst, last_refill=now)
                self._buckets[key] = bucket
            elapsed = now - bucket.last_refill
            bucket.tokens = min(burst, bucket.tokens + elapsed * tokens_per_second)
            bucket.last_refill = now
            if bucket.tokens < cost:
                return False
            bucket.tokens -= cost
            return True


# Lua script: atomic check-and-decrement on Redis. Stores
# (tokens, last_refill) as a hash; refill on read; deny if insufficient.
# Atomicity matters because two API replicas might otherwise both read
# 100 tokens, both decrement to 99, and effectively double the quota.
_REDIS_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local burst = tonumber(ARGV[1])
local tokens_per_second = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens
local last_refill
if bucket[1] == false then
  tokens = burst
  last_refill = now
else
  tokens = tonumber(bucket[1])
  last_refill = tonumber(bucket[2])
end

local elapsed = now - last_refill
if elapsed < 0 then elapsed = 0 end
tokens = math.min(burst, tokens + elapsed * tokens_per_second)

if tokens < cost then
  redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
  redis.call('EXPIRE', key, ttl)
  return 0
end

tokens = tokens - cost
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, ttl)
return 1
"""


class RedisRateLimitBackend:
    """Atomic Redis-backed token bucket using a Lua script.

    Bucket state survives process restart and is shared across replicas
    so a multi-pod deploy enforces a single global quota per tenant.
    The Lua script is registered once at construction; each ``consume``
    is one ``EVALSHA`` round-trip.

    The Redis client is injected to keep this module decoupled from a
    specific client library. Any object with a ``register_script`` and
    ``evalsha`` method (or compatible) works — the standard ``redis``
    package's ``Redis.register_script`` returns a callable script
    object that we call directly.
    """

    def __init__(
        self,
        client: object,
        *,
        key_prefix: str = "luvoire:rl:",
        bucket_ttl_seconds: int = 3600,
    ) -> None:
        if bucket_ttl_seconds <= 0:
            raise ValueError("bucket_ttl_seconds must be positive")
        if not key_prefix:
            raise ValueError("key_prefix must be non-empty")
        register = getattr(client, "register_script", None)
        if register is None:
            raise TypeError(
                "Redis client must expose register_script() — pass a "
                "redis.Redis or a compatible double"
            )
        self._client = client
        self._key_prefix = key_prefix
        self._ttl = bucket_ttl_seconds
        self._script = register(_REDIS_TOKEN_BUCKET_LUA)

    def consume(self, key: str, *, cost: float, tokens_per_second: float, burst: float) -> bool:
        full_key = f"{self._key_prefix}{key}"
        result = self._script(
            keys=[full_key],
            args=[burst, tokens_per_second, cost, time.time(), self._ttl],
        )
        # The Lua script returns 1 on success, 0 on rate-limit reject.
        return int(result) == 1


class RateLimiter:
    """Token-bucket rate limiter keyed by API key or client host.

    Defaults to an in-memory backend; pass ``backend=RedisRateLimitBackend(...)``
    for multi-replica deployments where bucket state must be shared.
    """

    def __init__(
        self,
        *,
        tokens_per_second: float = 100.0,
        burst: float = 100.0,
        backend: RateLimitBackend | None = None,
    ) -> None:
        if tokens_per_second < 0.0:
            raise ValueError("tokens_per_second must not be negative")
        if burst <= 0.0:
            raise ValueError("burst must be positive")
        self.tokens_per_second = tokens_per_second
        self.burst = burst
        self._backend: RateLimitBackend = backend or _InMemoryBackend()

    @classmethod
    def from_env(cls) -> RateLimiter:
        tokens_per_second = float(
            get_env(
                "LUVOIRE_RATE_LIMIT_TOKENS_PER_SECOND",
                "KNOEMA_RATE_LIMIT_TOKENS_PER_SECOND",
                "100",
            )
            or "100"
        )
        burst = float(
            get_env("LUVOIRE_RATE_LIMIT_BURST", "KNOEMA_RATE_LIMIT_BURST", "100") or "100"
        )
        return cls(tokens_per_second=tokens_per_second, burst=burst)

    def consume(self, key: str, *, cost: float = 1.0) -> bool:
        if cost <= 0.0:
            raise ValueError("cost must be positive")
        return self._backend.consume(
            key,
            cost=cost,
            tokens_per_second=self.tokens_per_second,
            burst=self.burst,
        )


def _identity_from_headers(authorization: str | None, client_host: str | None) -> str:
    if authorization:
        return authorization
    if client_host:
        return client_host
    return "anonymous"


def enforce_rate_limit(request: Request) -> None:
    limiter = request.app.state.rate_limiter
    key = _identity_from_headers(
        request.headers.get("Authorization"),
        None if request.client is None else request.client.host,
    )
    if not limiter.consume(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded.",
        )


def enforce_websocket_rate_limit(websocket: WebSocket) -> None:
    limiter = websocket.app.state.rate_limiter
    key = _identity_from_headers(
        websocket.headers.get("Authorization"),
        None if websocket.client is None else websocket.client.host,
    )
    if not limiter.consume(key):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Rate limit exceeded.",
        )


__all__ = [
    "RateLimitBackend",
    "RateLimiter",
    "RedisRateLimitBackend",
    "TokenBucket",
    "enforce_rate_limit",
    "enforce_websocket_rate_limit",
]
