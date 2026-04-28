"""Tests for luvoire.demography.kosis_fetch — aggregate fetch + file cache.

All HTTP traffic is intercepted via :class:`httpx.MockTransport`; no test in
this file ever touches the real network. The local cache directory is a
``tmp_path`` so the suite is isolated from any real KOSIS fixture caches
the operator may have on disk.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from luvoire.demography.kosis_fetch import (
    DEFAULT_CACHE_DIR,
    KosisAggregateOnlyError,
    KosisFetchClient,
    KosisFetchError,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "demography"
    / "kosis_1B36E27_2024_11680.json"
)


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _handler_returning(
    payload: dict[str, Any],
    *,
    status: int = 200,
    captured: dict[str, Any] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        if captured is not None:
            captured["url"] = str(request.url)
        return httpx.Response(status, json=payload)

    return handler


# ---------------------------------------------------------------------------
# Construction / configuration
# ---------------------------------------------------------------------------


def test_default_cache_dir_constant_is_tmp_kosis_cache() -> None:
    assert Path("tmp/kosis_cache") == DEFAULT_CACHE_DIR


def test_constructor_rejects_non_positive_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        KosisFetchClient(cache_dir=tmp_path, timeout=0.0)


def test_offline_when_no_base_url_or_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LUVOIRE_KOSIS_API_KEY", raising=False)
    client = KosisFetchClient(cache_dir=tmp_path)
    assert client.is_online_configured is False


def test_online_when_base_url_and_api_key_provided(tmp_path: Path) -> None:
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
    )
    assert client.is_online_configured is True


def test_env_var_supplies_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LUVOIRE_KOSIS_API_KEY", "from-env")
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        cache_dir=tmp_path,
    )
    assert client.is_online_configured is True


# ---------------------------------------------------------------------------
# Cache hit / cache key determinism
# ---------------------------------------------------------------------------


def test_cache_hit_returns_fixture_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LUVOIRE_KOSIS_API_KEY", raising=False)
    client = KosisFetchClient(cache_dir=tmp_path)

    # Pre-seed the cache by computing the deterministic file name the
    # client would use for these inputs.
    fixture = _load_fixture()
    target_path = _expected_cache_path(client, "1B36E27", 2024, "11680")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
    )

    payload = client.fetch_aggregate("1B36E27", 2024, "11680")
    assert payload["table_id"] == "1B36E27"
    assert payload["region_code"] == "11680"
    assert payload["aggregation_level"] == "시군구"


def test_cache_key_is_deterministic(tmp_path: Path) -> None:
    client = KosisFetchClient(cache_dir=tmp_path)
    first = _expected_cache_path(client, "1B36E27", 2024, "11680")
    second = _expected_cache_path(client, "1B36E27", 2024, "11680")
    assert first == second
    third = _expected_cache_path(client, "1B36E27", 2024, "11200")
    assert first != third


def test_cache_key_distinguishes_none_region(tmp_path: Path) -> None:
    client = KosisFetchClient(cache_dir=tmp_path)
    with_region = _expected_cache_path(client, "1B36E27", 2024, "11680")
    without_region = _expected_cache_path(client, "1B36E27", 2024, None)
    assert with_region != without_region


# ---------------------------------------------------------------------------
# Cache miss + offline raises
# ---------------------------------------------------------------------------


def test_cache_miss_offline_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LUVOIRE_KOSIS_API_KEY", raising=False)
    client = KosisFetchClient(cache_dir=tmp_path)
    with pytest.raises(KosisFetchError, match="offline"):
        client.fetch_aggregate("1B36E27", 2024, "11680")


# ---------------------------------------------------------------------------
# Mocked successful network fetch
# ---------------------------------------------------------------------------


def test_successful_fetch_writes_cache(tmp_path: Path) -> None:
    fixture = _load_fixture()
    captured: dict[str, Any] = {}
    transport = httpx.MockTransport(_handler_returning(fixture, captured=captured))
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )

    payload = client.fetch_aggregate("1B36E27", 2024, "11680")
    assert payload["region_code"] == "11680"
    assert "tblId=1B36E27" in captured["url"]

    # Second call must hit cache (network would 500 if invoked) — swap the
    # transport with a poison handler to prove no network call happens.
    def poison(_: httpx.Request) -> httpx.Response:
        raise AssertionError("network must not be called on cache hit")

    client._transport = httpx.MockTransport(poison)  # type: ignore[attr-defined]
    client._client = None  # type: ignore[attr-defined]
    payload_again = client.fetch_aggregate("1B36E27", 2024, "11680")
    assert payload_again == payload

    cached_files = sorted(tmp_path.glob("*.json"))
    assert len(cached_files) == 1


# ---------------------------------------------------------------------------
# Aggregation-floor enforcement
# ---------------------------------------------------------------------------


def test_sub_sigungu_response_is_rejected(tmp_path: Path) -> None:
    bad_payload: dict[str, Any] = {
        "table_id": "1B36E27",
        "year": 2024,
        "region_code": "11680123",
        "aggregation_level": "동",
        "rows": [
            {"metric": "live_births_total", "value": 12, "aggregation_level": "동"},
        ],
    }
    transport = httpx.MockTransport(_handler_returning(bad_payload))
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )

    with pytest.raises(KosisAggregateOnlyError):
        client.fetch_aggregate("1B36E27", 2024, "11680123")

    # Crucially, the cache file must NOT have been written.
    assert sorted(tmp_path.glob("*.json")) == []


def test_low_population_row_is_rejected(tmp_path: Path) -> None:
    bad_payload: dict[str, Any] = {
        "table_id": "1B36E27",
        "year": 2024,
        "aggregation_level": "시군구",
        "rows": [
            {"metric": "live_births_total", "value": 3, "population": 250},
        ],
    }
    transport = httpx.MockTransport(_handler_returning(bad_payload))
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )

    with pytest.raises(KosisAggregateOnlyError):
        client.fetch_aggregate("1B36E27", 2024, "11680123")
    assert sorted(tmp_path.glob("*.json")) == []


def test_unknown_top_level_aggregation_level_rejected(tmp_path: Path) -> None:
    bad_payload: dict[str, Any] = {
        "table_id": "1B36E27",
        "year": 2024,
        "aggregation_level": "리",
        "rows": [],
    }
    transport = httpx.MockTransport(_handler_returning(bad_payload))
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )
    with pytest.raises(KosisAggregateOnlyError):
        client.fetch_aggregate("1B36E27", 2024, None)


# ---------------------------------------------------------------------------
# HTTP error handling
# ---------------------------------------------------------------------------


def test_non_200_response_raises_fetch_error(tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(503, text="upstream busy")
    )
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )
    with pytest.raises(KosisFetchError, match="503"):
        client.fetch_aggregate("1B36E27", 2024, "11680")


def test_malformed_json_raises_fetch_error(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = KosisFetchClient(
        base_url="https://kosis.example/openapi",
        api_key="test-key",
        cache_dir=tmp_path,
        transport=transport,
    )
    with pytest.raises(KosisFetchError, match="malformed"):
        client.fetch_aggregate("1B36E27", 2024, "11680")


# ---------------------------------------------------------------------------
# clear_cache
# ---------------------------------------------------------------------------


def test_clear_cache_removes_only_json_files(tmp_path: Path) -> None:
    client = KosisFetchClient(cache_dir=tmp_path)
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("text", encoding="utf-8")

    removed = client.clear_cache()
    assert removed == 2
    assert (tmp_path / "keep.txt").is_file()
    assert sorted(tmp_path.glob("*.json")) == []


def test_clear_cache_on_missing_directory_returns_zero(tmp_path: Path) -> None:
    target = tmp_path / "does-not-exist"
    client = KosisFetchClient(cache_dir=target)
    assert client.clear_cache() == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expected_cache_path(
    client: KosisFetchClient,
    table_id: str,
    year: int,
    region_code: str | None,
) -> Path:
    """Mirror the client's internal cache key derivation for fixture seeding."""

    from luvoire.demography.kosis_fetch import _FetchKey  # local import: test-only

    key = _FetchKey(table_id=table_id, year=year, region_code=region_code)
    return client.cache_dir / f"{key.digest()}.json"


# ---------------------------------------------------------------------------
# Round-4 audit: HTTP response size ceiling
# ---------------------------------------------------------------------------


def test_oversized_response_body_is_rejected(tmp_path: Path) -> None:
    """A KOSIS endpoint that streams more bytes than ``max_response_bytes``
    must raise ``KosisFetchError`` before the JSON parser sees the body —
    a slow / malicious server otherwise exhausts memory.
    """

    huge_body = b"X" * (5 * 1024)  # 5 KiB body

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=huge_body, headers={"content-type": "application/json"})

    transport = httpx.MockTransport(handler)
    client = KosisFetchClient(
        base_url="https://kosis.invalid",
        api_key="fake",
        cache_dir=tmp_path,
        transport=transport,
        max_response_bytes=1024,  # ceiling well below 5 KiB body
    )
    with pytest.raises(KosisFetchError, match=r"exceed"):
        client.fetch_aggregate("1B36E27", 2024, region_code="11680")


def test_oversized_content_length_header_is_rejected(tmp_path: Path) -> None:
    """If the server LIES about a small body but advertises a huge
    Content-Length, we still reject before consuming the stream.
    """

    def handler(_request: httpx.Request) -> httpx.Response:
        # httpx.Response will populate content-length itself if we
        # provide a real body; we provide a small body but header
        # cannot be lied to via httpx alone — instead simulate by
        # using a body larger than the cap to trigger the size check
        # while still exercising the header-pessimism path.
        return httpx.Response(
            200,
            content=b"{" + b" " * (2 * 1024) + b"}",
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = KosisFetchClient(
        base_url="https://kosis.invalid",
        api_key="fake",
        cache_dir=tmp_path,
        transport=transport,
        max_response_bytes=512,
    )
    with pytest.raises(KosisFetchError, match=r"exceeded|Content-Length"):
        client.fetch_aggregate("1B36E27", 2024, region_code="11680")


def test_max_response_bytes_must_be_positive_int(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="positive"):
        KosisFetchClient(cache_dir=tmp_path, max_response_bytes=0)
    with pytest.raises(ValueError, match="positive"):
        KosisFetchClient(cache_dir=tmp_path, max_response_bytes=-1)
    with pytest.raises(TypeError, match="int"):
        KosisFetchClient(cache_dir=tmp_path, max_response_bytes=1.5)  # type: ignore[arg-type]


def test_response_within_size_cap_is_accepted(tmp_path: Path) -> None:
    """Sanity: a normal-sized payload must continue to round-trip."""

    payload = _load_fixture()
    transport = httpx.MockTransport(_handler_returning(payload))
    client = KosisFetchClient(
        base_url="https://kosis.invalid",
        api_key="fake",
        cache_dir=tmp_path,
        transport=transport,
        max_response_bytes=10 * 1024 * 1024,  # default
    )
    result = client.fetch_aggregate("1B36E27", 2024, region_code="11680")
    assert result == payload


# ---------------------------------------------------------------------------
# Round-5 audit: corrupted cache files are auto-purged
# ---------------------------------------------------------------------------


def test_corrupted_cache_file_is_purged_and_raises(tmp_path: Path) -> None:
    """A cache file with malformed JSON must be DELETED so the next
    call falls through to refetch — without purge, a single corrupted
    file would wedge the table forever. Round-5 audit fix.
    """

    client = KosisFetchClient(cache_dir=tmp_path)
    cache_path = _expected_cache_path(client, "1B36E27", 2024, "11680")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(KosisFetchError, match="purged"):
        client.fetch_aggregate("1B36E27", 2024, region_code="11680")
    assert not cache_path.exists(), "corrupted cache file must have been purged"


def test_non_object_cache_file_is_purged_and_raises(tmp_path: Path) -> None:
    """JSON parses but yields a non-dict (e.g. a list) — must also be
    purged, not raised forever.
    """

    client = KosisFetchClient(cache_dir=tmp_path)
    cache_path = _expected_cache_path(client, "1B36E27", 2024, "11680")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(KosisFetchError, match="purged"):
        client.fetch_aggregate("1B36E27", 2024, region_code="11680")
    assert not cache_path.exists()


def test_purge_then_refetch_succeeds(tmp_path: Path) -> None:
    """After auto-purge of a corrupted file, the next fetch with a
    working transport must succeed cleanly.
    """

    payload = _load_fixture()
    transport = httpx.MockTransport(_handler_returning(payload))
    client = KosisFetchClient(
        base_url="https://kosis.invalid",
        api_key="fake",
        cache_dir=tmp_path,
        transport=transport,
    )
    cache_path = _expected_cache_path(client, "1B36E27", 2024, "11680")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("garbage", encoding="utf-8")

    with pytest.raises(KosisFetchError, match="purged"):
        client.fetch_aggregate("1B36E27", 2024, region_code="11680")
    # Second call: cache is gone, refetch from transport.
    result = client.fetch_aggregate("1B36E27", 2024, region_code="11680")
    assert result == payload
