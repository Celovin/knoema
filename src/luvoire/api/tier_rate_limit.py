"""Tier-aware rate limiting for authenticated API tenants."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status

from luvoire.api.auth import AuthenticatedTenant, require_tenant
from luvoire.api.rate_limit import TokenBucket
from luvoire.billing.tiers import TierName
from luvoire.observability.metrics import record_rate_limit_hit


@dataclass(frozen=True, slots=True)
class TierRateLimit:
    requests_per_minute: float
    burst: float

    @property
    def tokens_per_second(self) -> float:
        return self.requests_per_minute / 60.0


@dataclass(frozen=True, slots=True)
class TierRateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


TIER_RATE_LIMITS: dict[TierName, TierRateLimit] = {
    "free": TierRateLimit(requests_per_minute=10.0, burst=20.0),
    "pro": TierRateLimit(requests_per_minute=120.0, burst=240.0),
    "team": TierRateLimit(requests_per_minute=600.0, burst=1200.0),
    "enterprise": TierRateLimit(requests_per_minute=6000.0, burst=12000.0),
}


class TierRateLimiter:
    """In-memory token buckets keyed by tenant and tier."""

    def __init__(self, *, time_fn: Callable[[], float] | None = None) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        self._time_fn = time_fn or time.monotonic

    def consume(self, tenant: AuthenticatedTenant, *, cost: float = 1.0) -> TierRateLimitResult:
        if cost <= 0.0:
            raise ValueError("cost must be positive")
        limit = TIER_RATE_LIMITS[tenant.tier]
        key = f"tier:{tenant.tier}|tenant:{tenant.tenant_id}"
        now = float(self._time_fn())
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(tokens=limit.burst, last_refill=now)
                self._buckets[key] = bucket
            elapsed = now - bucket.last_refill
            bucket.tokens = min(limit.burst, bucket.tokens + elapsed * limit.tokens_per_second)
            bucket.last_refill = now
            if bucket.tokens < cost:
                missing = cost - bucket.tokens
                retry_after = 60 if limit.tokens_per_second <= 0 else max(1, int(missing / limit.tokens_per_second))
                return TierRateLimitResult(
                    allowed=False,
                    remaining=max(0, int(bucket.tokens)),
                    retry_after_seconds=retry_after,
                )
            bucket.tokens -= cost
            return TierRateLimitResult(
                allowed=True,
                remaining=max(0, int(bucket.tokens)),
                retry_after_seconds=0,
            )


def enforce_tier_rate_limit(
    request: Request,
    response: Response,
    tenant: Annotated[AuthenticatedTenant, Depends(require_tenant)],
) -> AuthenticatedTenant:
    limiter = getattr(request.app.state, "tier_rate_limiter", None)
    if limiter is None:
        limiter = TierRateLimiter()
        request.app.state.tier_rate_limiter = limiter
    result = limiter.consume(tenant)
    response.headers["X-Luvoire-RateLimit-Tier"] = tenant.tier
    response.headers["X-Luvoire-RateLimit-Remaining"] = str(result.remaining)
    if not result.allowed:
        record_rate_limit_hit(tenant.tier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for tenant tier.",
            headers={
                "Retry-After": str(result.retry_after_seconds),
                "X-Luvoire-RateLimit-Tier": tenant.tier,
                "X-Luvoire-RateLimit-Remaining": str(result.remaining),
            },
        )
    return tenant


__all__ = [
    "TIER_RATE_LIMITS",
    "TierRateLimit",
    "TierRateLimitResult",
    "TierRateLimiter",
    "enforce_tier_rate_limit",
]
