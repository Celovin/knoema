"""Simple token-bucket rate limiting for the Luvoire API server."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request, WebSocket, WebSocketException, status

from luvoire.config import get_env


@dataclass(slots=True)
class TokenBucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """In-memory token-bucket rate limiter keyed by API key or client host."""

    def __init__(
        self,
        *,
        tokens_per_second: float = 100.0,
        burst: float = 100.0,
    ) -> None:
        if tokens_per_second < 0.0:
            raise ValueError("tokens_per_second must not be negative")
        if burst <= 0.0:
            raise ValueError("burst must be positive")
        self.tokens_per_second = tokens_per_second
        self.burst = burst
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

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
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(tokens=self.burst, last_refill=now)
                self._buckets[key] = bucket
            elapsed = now - bucket.last_refill
            bucket.tokens = min(self.burst, bucket.tokens + elapsed * self.tokens_per_second)
            bucket.last_refill = now
            if bucket.tokens < cost:
                return False
            bucket.tokens -= cost
            return True


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
    "RateLimiter",
    "TokenBucket",
    "enforce_rate_limit",
    "enforce_websocket_rate_limit",
]
