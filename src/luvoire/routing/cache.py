"""In-memory LRU cache for OSRM route responses.

The cache is intentionally tiny and dependency-free. It stores
:class:`luvoire.routing.osrm_client.RouteResponse` values keyed by a
deterministic string (see :func:`luvoire.routing.osrm_client.cache_key`).

Thread-safety is **not** required: the urban-grid simulation runs each route
lookup serially per agent and the cache is local to a single process. If a
caller mutates the cache from multiple threads, the ``OrderedDict.popitem``
loop in :meth:`LruCache.set` is **not** atomic with the surrounding
``move_to_end`` operations; callers MUST serialise access (e.g. with a
``threading.Lock``) or wrap the cache in their own thread-safe adapter.
The eviction loop is bounded by ``max_size`` so it cannot run forever, but
it can drop the wrong entries if a concurrent ``move_to_end`` reorders the
underlying ``OrderedDict`` mid-iteration.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from luvoire.routing.osrm_client import RouteResponse


@runtime_checkable
class Cache(Protocol):
    """Minimal protocol for a route-response cache.

    Implementations must be deterministic for identical key sequences and
    must never raise on cache misses; ``get`` returns ``None`` instead.
    """

    def get(self, key: str) -> RouteResponse | None: ...

    def set(self, key: str, value: RouteResponse) -> None: ...


class LruCache:
    """Bounded least-recently-used cache backed by ``OrderedDict``.

    Eviction policy: when ``len(cache) > max_size`` after a ``set``, the
    least-recently-used entry is dropped. Reading via ``get`` also marks the
    entry as recently used. ``hits`` and ``misses`` are exposed as read-only
    counters for observability.
    """

    def __init__(self, max_size: int = 4096) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be a positive integer")
        self._max_size: int = int(max_size)
        self._store: OrderedDict[str, RouteResponse] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def max_size(self) -> int:
        return self._max_size

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self._store

    def get(self, key: str) -> RouteResponse | None:
        value = self._store.get(key)
        if value is None:
            self._misses += 1
            return None
        # Mark as recently used.
        self._store.move_to_end(key)
        self._hits += 1
        return value

    def set(self, key: str, value: RouteResponse) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)


__all__ = ["Cache", "LruCache"]
