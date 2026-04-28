"""Round-6: Redis-backed rate-limit factory + in-memory contract.

We test the Redis backend with a fake Redis double that mirrors the
``register_script`` / callable-script contract — running a real Redis
in CI is out of scope for this audit pass.
"""

from __future__ import annotations

import pytest

from luvoire.api.rate_limit import (
    RateLimitBackend,
    RateLimiter,
    RedisRateLimitBackend,
)

# ---- Backend protocol contract ---------------------------------------


def test_default_rate_limiter_uses_in_memory_backend() -> None:
    """Constructing without an explicit ``backend`` must keep the
    historical in-memory behavior so existing tests / single-process
    deploys are unchanged.
    """

    limiter = RateLimiter(tokens_per_second=1.0, burst=2.0)
    # First two calls succeed, third is rejected (burst=2).
    assert limiter.consume("k") is True
    assert limiter.consume("k") is True
    assert limiter.consume("k") is False


# ---- Redis backend: fake client double ------------------------------


class _FakeScript:
    """Deterministic double for the Lua-evalsha script object.

    Implements the same external contract as
    ``redis.client.Script.__call__(keys=..., args=...)`` — this lets
    the test exercise ``RedisRateLimitBackend`` end-to-end without a
    real Redis. The token bucket math is intentionally replicated here
    so the backend's contract (atomic read-modify-write over Lua) is
    what's being tested, not the math.
    """

    def __init__(self, store: dict[str, dict[str, float]]) -> None:
        self._store = store

    def __call__(self, *, keys: list[str], args: list[float]) -> int:
        key = keys[0]
        burst = float(args[0])
        rate = float(args[1])
        cost = float(args[2])
        now = float(args[3])
        bucket = self._store.get(key)
        if bucket is None:
            tokens = burst
            last_refill = now
        else:
            tokens = bucket["tokens"]
            last_refill = bucket["last_refill"]
        elapsed = max(0.0, now - last_refill)
        tokens = min(burst, tokens + elapsed * rate)
        if tokens < cost:
            self._store[key] = {"tokens": tokens, "last_refill": now}
            return 0
        tokens -= cost
        self._store[key] = {"tokens": tokens, "last_refill": now}
        return 1


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, float]] = {}
        self.script_source: str | None = None

    def register_script(self, source: str) -> _FakeScript:
        self.script_source = source
        return _FakeScript(self.store)


def test_redis_backend_consume_succeeds_within_burst() -> None:
    fake = _FakeRedis()
    limiter = RateLimiter(
        tokens_per_second=1.0,
        burst=3.0,
        backend=RedisRateLimitBackend(fake),
    )
    assert limiter.consume("tenant-a") is True
    assert limiter.consume("tenant-a") is True
    assert limiter.consume("tenant-a") is True


def test_redis_backend_rejects_when_bucket_empty() -> None:
    fake = _FakeRedis()
    limiter = RateLimiter(
        tokens_per_second=0.0,  # no refill within test window
        burst=1.0,
        backend=RedisRateLimitBackend(fake),
    )
    assert limiter.consume("tenant-b") is True
    assert limiter.consume("tenant-b") is False


def test_redis_backend_keys_are_namespaced() -> None:
    """Different tenants MUST get independent buckets via the
    ``key_prefix`` namespace, not collide on raw user-supplied keys.
    """

    fake = _FakeRedis()
    backend = RedisRateLimitBackend(fake, key_prefix="luvoire:rl:")
    limiter = RateLimiter(tokens_per_second=0.0, burst=1.0, backend=backend)
    assert limiter.consume("tenant-x") is True
    assert limiter.consume("tenant-y") is True
    # Both buckets exist under the prefixed namespace.
    assert "luvoire:rl:tenant-x" in fake.store
    assert "luvoire:rl:tenant-y" in fake.store


def test_redis_backend_rejects_invalid_ttl() -> None:
    fake = _FakeRedis()
    with pytest.raises(ValueError, match="positive"):
        RedisRateLimitBackend(fake, bucket_ttl_seconds=0)


def test_redis_backend_rejects_empty_prefix() -> None:
    fake = _FakeRedis()
    with pytest.raises(ValueError, match="non-empty"):
        RedisRateLimitBackend(fake, key_prefix="")


def test_redis_backend_rejects_client_without_register_script() -> None:
    class _Bad:
        pass

    with pytest.raises(TypeError, match="register_script"):
        RedisRateLimitBackend(_Bad())


def test_backend_protocol_runtime_check() -> None:
    """``RateLimitBackend`` is a Protocol — the in-memory and Redis
    backends both satisfy it without ``@runtime_checkable``."""

    fake = _FakeRedis()
    backend: RateLimitBackend = RedisRateLimitBackend(fake)
    # Static check: this assigns without mypy error in the source tree.
    # Runtime: just confirm consume() is callable with the right shape.
    result = backend.consume(
        "k", cost=1.0, tokens_per_second=1.0, burst=1.0
    )
    assert isinstance(result, bool)


def test_backend_lua_script_is_registered_on_construction() -> None:
    """The Lua script must be registered once at backend construction
    so each ``consume`` is a single ``EVALSHA`` round-trip, not a fresh
    ``EVAL`` (which sends the full source every call).
    """

    fake = _FakeRedis()
    RedisRateLimitBackend(fake)
    assert fake.script_source is not None
    assert "HMGET" in fake.script_source
    assert "math.min" in fake.script_source
