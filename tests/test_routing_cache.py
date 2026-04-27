"""Tests for luvoire.routing.cache — bounded in-memory LRU cache."""

from __future__ import annotations

import pytest

from luvoire.routing import Cache, LruCache, RouteResponse


def _response(duration: float = 60.0, distance: float = 1000.0) -> RouteResponse:
    return RouteResponse(
        duration_seconds=duration,
        distance_meters=distance,
        geometry=None,
    )


def test_lru_cache_get_miss_returns_none_and_increments_misses() -> None:
    cache = LruCache(max_size=4)
    assert cache.get("nope") is None
    assert cache.misses == 1
    assert cache.hits == 0


def test_lru_cache_set_then_get_is_a_hit() -> None:
    cache = LruCache(max_size=4)
    value = _response()
    cache.set("k1", value)
    assert cache.get("k1") == value
    assert cache.hits == 1
    assert cache.misses == 0
    assert len(cache) == 1


def test_lru_cache_overwrite_does_not_grow_size() -> None:
    cache = LruCache(max_size=4)
    cache.set("k1", _response(duration=1.0))
    cache.set("k1", _response(duration=2.0))
    assert len(cache) == 1
    fetched = cache.get("k1")
    assert fetched is not None
    assert fetched.duration_seconds == 2.0


def test_lru_cache_evicts_least_recently_used() -> None:
    cache = LruCache(max_size=2)
    cache.set("a", _response(duration=1.0))
    cache.set("b", _response(duration=2.0))
    # Touch "a" so "b" becomes the LRU entry.
    assert cache.get("a") is not None
    cache.set("c", _response(duration=3.0))

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert len(cache) == 2


def test_lru_cache_overflow_drops_oldest_when_no_reads() -> None:
    cache = LruCache(max_size=3)
    for i in range(5):
        cache.set(f"k{i}", _response(duration=float(i)))
    # Only the last three writes survive.
    assert len(cache) == 3
    assert "k0" not in cache
    assert "k1" not in cache
    assert "k2" in cache
    assert "k3" in cache
    assert "k4" in cache


def test_lru_cache_rejects_non_positive_max_size() -> None:
    with pytest.raises(ValueError):
        LruCache(max_size=0)
    with pytest.raises(ValueError):
        LruCache(max_size=-1)


def test_lru_cache_stats_track_mixed_access() -> None:
    cache = LruCache(max_size=8)
    cache.set("k", _response())
    cache.get("k")  # hit
    cache.get("k")  # hit
    cache.get("missing")  # miss
    cache.get("also-missing")  # miss
    assert cache.hits == 2
    assert cache.misses == 2


def test_lru_cache_satisfies_protocol() -> None:
    cache: Cache = LruCache(max_size=2)
    cache.set("x", _response(duration=7.5))
    fetched = cache.get("x")
    assert fetched is not None
    assert fetched.duration_seconds == 7.5
