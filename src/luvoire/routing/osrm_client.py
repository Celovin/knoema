"""Deterministic OSRM routing client for the synthetic urban grid.

OSRM is consumed only via HTTP from a sidecar process; this module never
spawns subprocesses and never reaches a real network in tests. All transport
behaviour is injectable via :class:`httpx.HTTPTransport` (or
:class:`httpx.MockTransport` in tests) so simulation runs stay reproducible.

The realism roadmap calls for cache keys that bucket origin/destination by
H3 cell and depart-time by hour. We do not depend on H3 here — the urban grid
keeps raw lat/lon — so :func:`cache_key` produces a stable SHA-256 over the
canonical JSON of the request fields. The H3 reduction can be applied
upstream by callers without changing this module.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Literal, cast

import httpx

from luvoire.routing.cache import Cache

RoutingMode = Literal["driving", "walking", "cycling"]
_VALID_MODES: frozenset[str] = frozenset({"driving", "walking", "cycling"})


class RoutingUnavailable(RuntimeError):  # noqa: N818 — name is part of public API
    """Raised when the OSRM sidecar is unreachable or returns a non-OK reply.

    Callers in the simulation must surface this as a hard failure rather than
    silently substituting a zero-duration route, which would corrupt outcome
    statistics.
    """


@dataclass(frozen=True, slots=True)
class OsrmConfig:
    """Static configuration for the OSRM client."""

    base_url: str
    timeout_seconds: float = 5.0
    mode: RoutingMode = "driving"

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("base_url must be a non-empty string")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(_VALID_MODES)}")


@dataclass(frozen=True, slots=True)
class RouteRequest:
    """A single origin->destination route lookup at a given hour bucket."""

    origin: tuple[float, float]
    destination: tuple[float, float]
    mode: RoutingMode
    depart_at_hour: int

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(_VALID_MODES)}")
        if not (0 <= self.depart_at_hour <= 23):
            raise ValueError("depart_at_hour must be in [0, 23]")
        for label, point in (("origin", self.origin), ("destination", self.destination)):
            if len(point) != 2:
                raise ValueError(f"{label} must be a (lat, lon) pair")
            lat, lon = point
            # Reject NaN / inf explicitly. The bound checks below also reject
            # them (any comparison with NaN is False) but we want a clearer
            # error message for the audit trail.
            if not (math.isfinite(lat) and math.isfinite(lon)):
                raise ValueError(f"{label} must contain finite coordinates")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"{label} latitude must be in [-90, 90]")
            if not (-180.0 <= lon <= 180.0):
                raise ValueError(f"{label} longitude must be in [-180, 180]")


@dataclass(frozen=True, slots=True)
class RouteResponse:
    """Parsed OSRM route reply.

    ``geometry`` holds the encoded polyline if OSRM returned one (i.e. the
    caller asked for ``overview != "false"``); the default client uses
    ``overview=false`` so this field is normally ``None``.
    """

    duration_seconds: float
    distance_meters: float
    geometry: str | None


def cache_key(request: RouteRequest) -> str:
    """Return a stable SHA-256 hex digest of ``request``'s canonical JSON.

    The key is deterministic across processes and Python versions: the JSON
    is sorted by key, uses no whitespace, and only contains JSON-native
    scalar types. Floats round-trip through ``json.dumps`` deterministically
    for IEEE-754 doubles, which is what numpy/python use natively.
    """
    payload: dict[str, Any] = {
        "origin": [float(request.origin[0]), float(request.origin[1])],
        "destination": [float(request.destination[0]), float(request.destination[1])],
        "mode": request.mode,
        "depart_at_hour": int(request.depart_at_hour),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OsrmClient:
    """Synchronous OSRM HTTP client with optional response caching.

    The client owns its :class:`httpx.Client`. A custom ``transport`` may be
    injected for testing (e.g. :class:`httpx.MockTransport`); production
    callers will normally rely on the default transport which speaks HTTP to
    a co-located OSRM sidecar.
    """

    def __init__(
        self,
        config: OsrmConfig,
        *,
        transport: httpx.HTTPTransport | httpx.MockTransport | None = None,
        cache: Cache | None = None,
    ) -> None:
        self._config = config
        self._cache = cache
        self._client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
            transport=transport,
        )

    @property
    def config(self) -> OsrmConfig:
        return self._config

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OsrmClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def route(self, request: RouteRequest) -> RouteResponse:
        """Look up ``request`` in cache or fetch it from the OSRM sidecar."""
        key = cache_key(request)
        if self._cache is not None:
            hit = self._cache.get(key)
            if hit is not None:
                return hit

        response = self._fetch(request)

        if self._cache is not None:
            self._cache.set(key, response)
        return response

    def _fetch(self, request: RouteRequest) -> RouteResponse:
        # OSRM expects coordinates in lon,lat order.
        olat, olon = request.origin
        dlat, dlon = request.destination
        path = (
            f"/route/v1/{request.mode}/"
            f"{olon:.6f},{olat:.6f};{dlon:.6f},{dlat:.6f}"
        )
        try:
            http_response = self._client.get(path, params={"overview": "false"})
        except httpx.HTTPError as exc:
            raise RoutingUnavailable(
                f"OSRM transport error for {request.mode} route: {exc}"
            ) from exc

        if http_response.status_code != 200:
            raise RoutingUnavailable(
                f"OSRM returned HTTP {http_response.status_code} for {request.mode} route"
            )

        try:
            payload = http_response.json()
        except ValueError as exc:
            raise RoutingUnavailable(
                f"OSRM returned malformed JSON: {exc}"
            ) from exc

        return _parse_route_payload(payload)


def _parse_route_payload(payload: object) -> RouteResponse:
    """Validate and project an OSRM JSON payload to :class:`RouteResponse`."""
    if not isinstance(payload, dict):
        raise RoutingUnavailable("OSRM payload is not a JSON object")

    code = payload.get("code")
    if code != "Ok":
        raise RoutingUnavailable(f"OSRM responded with code={code!r}")

    routes_raw = payload.get("routes")
    if not isinstance(routes_raw, list) or not routes_raw:
        raise RoutingUnavailable("OSRM payload contains no routes")

    first = routes_raw[0]
    if not isinstance(first, dict):
        raise RoutingUnavailable("OSRM route entry is not an object")

    duration = first.get("duration")
    distance = first.get("distance")
    if not isinstance(duration, int | float) or not isinstance(distance, int | float):
        raise RoutingUnavailable(
            "OSRM route entry missing numeric duration/distance fields"
        )

    geometry_raw = first.get("geometry")
    geometry: str | None
    if geometry_raw is None:
        geometry = None
    elif isinstance(geometry_raw, str):
        geometry = geometry_raw
    else:
        # Non-string geometry (e.g. a GeoJSON dict) is unexpected for our
        # default overview=false call. Treat it as absent rather than
        # corrupting the cached response.
        geometry = None

    return RouteResponse(
        duration_seconds=float(cast(float, duration)),
        distance_meters=float(cast(float, distance)),
        geometry=geometry,
    )


__all__ = [
    "OsrmClient",
    "OsrmConfig",
    "RouteRequest",
    "RouteResponse",
    "RoutingMode",
    "RoutingUnavailable",
    "cache_key",
]
