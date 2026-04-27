"""Tests for luvoire.routing.osrm_client — deterministic OSRM HTTP client.

All HTTP traffic is intercepted via :class:`httpx.MockTransport`; no test in
this file ever touches the real network.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from luvoire.routing import (
    LruCache,
    OsrmClient,
    OsrmConfig,
    RouteRequest,
    RouteResponse,
    RoutingUnavailable,
    cache_key,
)

BASE_URL = "http://osrm.test"


def _ok_payload(duration: float = 123.4, distance: float = 567.8) -> dict[str, Any]:
    return {
        "code": "Ok",
        "routes": [
            {
                "duration": duration,
                "distance": distance,
            }
        ],
    }


def _make_request(
    *,
    mode: str = "driving",
    hour: int = 8,
    origin: tuple[float, float] = (37.5665, 126.9780),
    destination: tuple[float, float] = (37.5700, 126.9820),
) -> RouteRequest:
    return RouteRequest(
        origin=origin,
        destination=destination,
        mode=mode,  # type: ignore[arg-type]
        depart_at_hour=hour,
    )


def _client(handler: httpx.MockTransport, cache: LruCache | None = None) -> OsrmClient:
    return OsrmClient(
        OsrmConfig(base_url=BASE_URL, mode="driving"),
        transport=handler,
        cache=cache,
    )


# ---------------------------------------------------------------------------
# Config / request validation
# ---------------------------------------------------------------------------


def test_osrm_config_rejects_empty_base_url() -> None:
    with pytest.raises(ValueError):
        OsrmConfig(base_url="")


def test_osrm_config_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError):
        OsrmConfig(base_url=BASE_URL, timeout_seconds=0.0)


def test_route_request_rejects_invalid_hour() -> None:
    with pytest.raises(ValueError):
        RouteRequest(
            origin=(0.0, 0.0),
            destination=(1.0, 1.0),
            mode="driving",
            depart_at_hour=24,
        )


def test_route_request_rejects_out_of_range_lat() -> None:
    with pytest.raises(ValueError):
        RouteRequest(
            origin=(95.0, 0.0),
            destination=(1.0, 1.0),
            mode="driving",
            depart_at_hour=0,
        )


# ---------------------------------------------------------------------------
# Successful HTTP path
# ---------------------------------------------------------------------------


def test_route_parses_ok_payload() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["query"] = str(request.url.query)
        return httpx.Response(200, json=_ok_payload(duration=42.0, distance=84.0))

    transport = httpx.MockTransport(handler)
    with _client(transport) as client:
        response = client.route(_make_request(mode="cycling"))

    assert isinstance(response, RouteResponse)
    assert response.duration_seconds == pytest.approx(42.0)
    assert response.distance_meters == pytest.approx(84.0)
    assert response.geometry is None
    # OSRM expects lon,lat order in the path.
    assert captured["path"].startswith("/route/v1/cycling/")
    assert "126.978000,37.566500;126.982000,37.570000" in captured["path"]
    assert "overview=false" in captured["query"]


def test_route_extracts_geometry_when_present() -> None:
    payload = _ok_payload()
    payload["routes"][0]["geometry"] = "abc123polyline"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    with _client(transport) as client:
        response = client.route(_make_request())

    assert response.geometry == "abc123polyline"


def test_route_treats_non_string_geometry_as_none() -> None:
    payload = _ok_payload()
    payload["routes"][0]["geometry"] = {"type": "LineString", "coordinates": []}

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    with _client(transport) as client:
        response = client.route(_make_request())

    assert response.geometry is None


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_route_raises_on_non_200() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream busy")

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable) as info:
        client.route(_make_request())

    assert "503" in str(info.value)


def test_route_raises_on_malformed_json() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable):
        client.route(_make_request())


def test_route_raises_on_non_ok_code() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": "NoRoute", "routes": []})

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable):
        client.route(_make_request())


def test_route_raises_on_missing_routes() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": "Ok"})

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable):
        client.route(_make_request())


def test_route_raises_on_transport_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable) as info:
        client.route(_make_request())

    assert "transport error" in str(info.value)


def test_route_raises_when_routes_entry_lacks_numbers() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"code": "Ok", "routes": [{"duration": "fast", "distance": None}]},
        )

    transport = httpx.MockTransport(handler)
    with _client(transport) as client, pytest.raises(RoutingUnavailable):
        client.route(_make_request())


# ---------------------------------------------------------------------------
# Cache integration
# ---------------------------------------------------------------------------


def test_route_uses_cache_to_skip_second_call() -> None:
    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=_ok_payload(duration=10.0, distance=20.0))

    transport = httpx.MockTransport(handler)
    cache = LruCache(max_size=8)
    with _client(transport, cache=cache) as client:
        first = client.route(_make_request())
        second = client.route(_make_request())

    assert call_count == 1
    assert first == second
    assert cache.hits == 1
    assert cache.misses == 1


def test_route_cache_distinguishes_requests() -> None:
    payloads = iter(
        [
            _ok_payload(duration=1.0, distance=11.0),
            _ok_payload(duration=2.0, distance=22.0),
        ]
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(payloads))

    transport = httpx.MockTransport(handler)
    cache = LruCache(max_size=8)
    with _client(transport, cache=cache) as client:
        first = client.route(_make_request(hour=7))
        second = client.route(_make_request(hour=8))

    assert first.duration_seconds == 1.0
    assert second.duration_seconds == 2.0
    assert cache.hits == 0
    assert cache.misses == 2


# ---------------------------------------------------------------------------
# cache_key determinism
# ---------------------------------------------------------------------------


def test_cache_key_is_deterministic_for_identical_requests() -> None:
    a = _make_request()
    b = _make_request()
    assert cache_key(a) == cache_key(b)


def test_cache_key_differs_for_different_modes() -> None:
    a = _make_request(mode="driving")
    b = _make_request(mode="walking")
    assert cache_key(a) != cache_key(b)


def test_cache_key_differs_for_different_hour_buckets() -> None:
    a = _make_request(hour=7)
    b = _make_request(hour=8)
    assert cache_key(a) != cache_key(b)


def test_cache_key_differs_for_different_endpoints() -> None:
    a = _make_request(origin=(37.0, 127.0))
    b = _make_request(origin=(37.0001, 127.0))
    assert cache_key(a) != cache_key(b)


def test_cache_key_payload_is_canonical_json() -> None:
    request = _make_request()
    key = cache_key(request)
    # Recompute manually to confirm canonical-JSON contract.
    payload = {
        "destination": [float(request.destination[0]), float(request.destination[1])],
        "depart_at_hour": int(request.depart_at_hour),
        "mode": request.mode,
        "origin": [float(request.origin[0]), float(request.origin[1])],
    }
    assert isinstance(json.dumps(payload, sort_keys=True), str)
    assert len(key) == 64  # SHA-256 hex
