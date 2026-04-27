"""Deterministic OSRM routing client for the synthetic urban grid.

This subpackage provides a tiny HTTP client over OSRM
(`Open Source Routing Machine <https://project-osrm.org>`_) plus an in-memory
LRU response cache. OSRM is consumed via HTTP from a sidecar; this module
never spawns processes and never reaches a real network in tests.

Public surface:

- :class:`OsrmConfig` and :class:`RouteRequest` configure a lookup.
- :class:`OsrmClient` performs the actual HTTP call and parses replies into
  :class:`RouteResponse`.
- :class:`Cache` plus :class:`LruCache` provide a deterministic, bounded,
  in-process cache keyed by :func:`cache_key`.
- :class:`RoutingUnavailable` is raised on any transport or parse failure;
  the client never silently substitutes zero-duration routes.
"""

from luvoire.routing.cache import Cache, LruCache
from luvoire.routing.osrm_client import (
    OsrmClient,
    OsrmConfig,
    RouteRequest,
    RouteResponse,
    RoutingMode,
    RoutingUnavailable,
    cache_key,
)

__all__ = [
    "Cache",
    "LruCache",
    "OsrmClient",
    "OsrmConfig",
    "RouteRequest",
    "RouteResponse",
    "RoutingMode",
    "RoutingUnavailable",
    "cache_key",
]
