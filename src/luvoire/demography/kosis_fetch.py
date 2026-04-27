"""KOSIS aggregate fetch + local file cache layer (no microdata).

This module wraps the *aggregate* KOSIS open-data endpoints (시군구·시도·전국
집계만) behind a deterministic file cache. Per the
:mod:`luvoire.demography` Civilian Use Policy, the engine never downloads
or parses individual-level microdata: every response that contains a
sub-시군구 aggregation level (동·읍·면) is rejected with
:class:`KosisAggregateOnlyError` before the cache is written.

The fetch layer is **optional online**. If neither ``base_url`` nor
``api_key`` is configured at runtime the client refuses to issue any
network call and only serves cache hits (e.g. fixture JSON dropped in by
operators or tests). This keeps the module importable on air-gapped CI
machines and inside ``luvoire.demography.__init__`` without forcing a
dependency on a live KOSIS endpoint.

All HTTP traffic is routed through :class:`httpx.Client` and may be
intercepted via :class:`httpx.MockTransport` from tests; nothing in this
file talks to the real network on its own.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

DEFAULT_CACHE_DIR = Path("tmp/kosis_cache")
"""Default on-disk cache root, relative to the working directory."""

_DEFAULT_TIMEOUT_SECONDS = 10.0

_DEFAULT_MAX_RESPONSE_BYTES: int = 10 * 1024 * 1024
"""Default cap on a single KOSIS response body (10 MiB).

Without this cap a slow / malicious server (or a MITM that stripped TLS
on a misconfigured network) could stream gigabytes into ``response.json``
and exhaust memory on a low-resource scenario runner. The KOSIS aggregate
endpoints we use return well under 1 MiB for any single (table, year)
fetch in the registry; a 10 MiB ceiling leaves a wide safety margin
without truncating legitimate payloads.
"""

_FORBIDDEN_AGGREGATION_LEVELS: frozenset[str] = frozenset({"동", "읍", "면"})
"""Sub-시군구 administrative units that violate the aggregate-only floor."""

_ALLOWED_AGGREGATION_LEVELS: frozenset[str] = frozenset({"시군구", "시도", "전국"})
"""Administrative aggregation levels that the registry permits."""

_MIN_ROW_POPULATION = 10_000
"""Lower bound on the population denominator that constitutes an aggregate.

A row whose ``population`` field falls below this threshold is treated as
sub-시군구 microdata and rejected even if it does not carry an explicit
``aggregation_level`` field.
"""


class KosisFetchError(RuntimeError):
    """Raised when the KOSIS fetch layer cannot satisfy a request.

    This covers offline configuration (missing ``base_url``/``api_key``),
    HTTP transport failures, non-200 responses, and malformed JSON. It does
    **not** cover aggregate-floor violations, which raise
    :class:`KosisAggregateOnlyError` so the caller can distinguish a policy
    rejection from a transient network problem.
    """


class KosisAggregateOnlyError(ValueError):
    """Raised when a KOSIS response contains sub-시군구 aggregation rows.

    The Civilian Use Policy of :mod:`luvoire.demography` forbids storing,
    caching, or returning per-동·읍·면 records. The fetch layer therefore
    rejects such responses *before* writing the cache file, so a poisoned
    payload cannot be replayed from disk on subsequent runs.
    """


@dataclass(frozen=True, slots=True)
class _FetchKey:
    """Internal canonical representation of a cache key."""

    table_id: str
    year: int
    region_code: str | None

    def digest(self) -> str:
        payload = {
            "table_id": self.table_id,
            "year": int(self.year),
            "region_code": self.region_code,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _coerce_cache_dir(cache_dir: Path | str) -> Path:
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)
    if not isinstance(cache_dir, Path):
        raise TypeError(
            f"cache_dir must be a Path or str (got {type(cache_dir).__name__})"
        )
    return cache_dir


class KosisFetchClient:
    """Aggregate-only KOSIS fetch client with a deterministic file cache.

    The client owns its :class:`httpx.Client` instance. A custom
    ``transport`` may be injected for testing; production callers will
    typically rely on the default transport which speaks HTTPS to KOSIS.

    The cache is a flat directory of JSON blobs keyed by SHA-256 of
    ``(table_id, year, region_code)``. Cache lookups never trigger a
    network call, so fixture JSON dropped into ``cache_dir`` becomes a
    fully offline data source.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        transport: httpx.HTTPTransport | httpx.MockTransport | None = None,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if not isinstance(max_response_bytes, int) or isinstance(max_response_bytes, bool):
            raise TypeError("max_response_bytes must be an int")
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")

        self._base_url = (base_url or "").rstrip("/") or None
        self._api_key = api_key or os.environ.get("LUVOIRE_KOSIS_API_KEY") or None
        self._timeout = float(timeout)
        self._cache_dir = _coerce_cache_dir(cache_dir)
        self._max_response_bytes = max_response_bytes

        # We construct the httpx.Client lazily on first network use so that
        # purely cache-hit workflows do not even allocate a transport. The
        # MockTransport injection still needs to be remembered up front.
        self._transport = transport
        self._client: httpx.Client | None = None

    # ------------------------------------------------------------------ utils
    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def is_online_configured(self) -> bool:
        """Return ``True`` iff a real network fetch could be attempted.

        A test ``transport`` (e.g. :class:`httpx.MockTransport`) counts as
        online for the purposes of this check, since it can serve responses
        without a configured ``base_url``/``api_key`` pair.
        """

        if self._transport is not None:
            return True
        return self._base_url is not None and self._api_key is not None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> KosisFetchClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --------------------------------------------------------------- caching
    def _cache_path(self, key: _FetchKey) -> Path:
        return self._cache_dir / f"{key.digest()}.json"

    def _read_cache(self, path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KosisFetchError(
                f"failed to read KOSIS cache file {path}: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise KosisFetchError(
                f"KOSIS cache file {path} did not contain a JSON object"
            )
        return data

    def _write_cache(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(path)

    def clear_cache(self) -> int:
        """Delete every ``*.json`` file in the cache directory.

        Returns the number of files removed. Missing directories are
        treated as empty caches and produce a count of zero.
        """

        if not self._cache_dir.is_dir():
            return 0
        removed = 0
        for entry in self._cache_dir.iterdir():
            if entry.is_file() and entry.suffix == ".json":
                entry.unlink()
                removed += 1
        return removed

    # ---------------------------------------------------------------- public
    def fetch_aggregate(
        self,
        table_id: str,
        year: int,
        region_code: str | None = None,
    ) -> dict[str, Any]:
        """Return the aggregate KOSIS payload for ``(table_id, year, region_code)``.

        Cache hits short-circuit any network access. Cache misses require
        an online configuration (or an injected ``transport``) and validate
        the response strictly: any sub-시군구 row triggers
        :class:`KosisAggregateOnlyError` and the cache file is **not**
        written.
        """

        if not isinstance(table_id, str) or not table_id:
            raise ValueError("table_id must be a non-empty string")
        if not isinstance(year, int) or isinstance(year, bool):
            raise ValueError("year must be an int")
        if region_code is not None and (
            not isinstance(region_code, str) or not region_code
        ):
            raise ValueError("region_code must be a non-empty string when provided")

        key = _FetchKey(table_id=table_id, year=year, region_code=region_code)
        cache_path = self._cache_path(key)

        cached = self._read_cache(cache_path)
        if cached is not None:
            # A poisoned cache file (e.g. hand-edited) must still be
            # rejected by the same validator that protects fresh fetches.
            _validate_aggregate_payload(cached)
            return cached

        if not self.is_online_configured:
            raise KosisFetchError(
                "KOSIS fetch client is offline: cache miss for "
                f"{table_id!r} year={year} region_code={region_code!r} "
                "and no base_url/api_key/transport configured. "
                "Drop a fixture JSON into the cache directory or set "
                "LUVOIRE_KOSIS_API_KEY."
            )

        payload = self._fetch_remote(key)
        _validate_aggregate_payload(payload)
        self._write_cache(cache_path, payload)
        return payload

    # --------------------------------------------------------------- network
    def _ensure_client(self) -> httpx.Client:
        if self._client is None:
            base_url = self._base_url or ""
            self._client = httpx.Client(
                base_url=base_url,
                timeout=self._timeout,
                transport=self._transport,
            )
        return self._client

    def _fetch_remote(self, key: _FetchKey) -> dict[str, Any]:
        client = self._ensure_client()
        params: dict[str, str] = {
            "tblId": key.table_id,
            "prdSe": "Y",
            "startPrdDe": str(key.year),
            "endPrdDe": str(key.year),
            "format": "json",
        }
        if key.region_code is not None:
            params["objL1"] = key.region_code

        # The api_key travels in an Authorization-like header rather
        # than the URL query string so it does not appear in HTTP access
        # logs, mocked-call captures, or KosisFetchError messages.
        headers: dict[str, str] = {}
        if self._api_key is not None:
            headers["X-Kosis-Api-Key"] = self._api_key

        try:
            response = client.get(
                "/statisticsData.do", params=params, headers=headers
            )
        except httpx.HTTPError as exc:
            raise KosisFetchError(
                f"KOSIS transport error for table {key.table_id!r}: {exc}"
            ) from exc

        if response.status_code != 200:
            raise KosisFetchError(
                f"KOSIS returned HTTP {response.status_code} for table {key.table_id!r}"
            )

        # Pre-body Content-Length check: when the server advertises a
        # body larger than our cap, abort BEFORE accessing ``response.content``
        # (which would force httpx to buffer the entire stream into RAM).
        # Round-2 audit moved this check ahead of ``.content`` to truly
        # bound memory rather than only bound JSON-parser exposure.
        declared = response.headers.get("content-length")
        if declared is not None:
            try:
                declared_int = int(declared)
            except ValueError:
                declared_int = None
            if declared_int is not None and declared_int > self._max_response_bytes:
                raise KosisFetchError(
                    f"KOSIS Content-Length {declared_int} exceeds "
                    f"{self._max_response_bytes} for table {key.table_id!r}"
                )

        # Defense-in-depth: a server that omits Content-Length (chunked
        # encoding) can still over-deliver. ``.content`` does buffer the
        # body, but we re-check the actual length post-buffer so the
        # subsequent JSON parse doesn't double the memory footprint.
        body = response.content
        if len(body) > self._max_response_bytes:
            raise KosisFetchError(
                f"KOSIS response for table {key.table_id!r} exceeded "
                f"{self._max_response_bytes} bytes "
                f"(got {len(body)}); refusing to parse"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise KosisFetchError(
                f"KOSIS returned malformed JSON for table {key.table_id!r}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise KosisFetchError(
                f"KOSIS payload for table {key.table_id!r} is not a JSON object"
            )
        return payload


def _iter_rows(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    rows = payload.get("rows")
    if rows is None:
        return ()
    if not isinstance(rows, list):
        raise KosisFetchError("KOSIS payload 'rows' field is not a list")
    typed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise KosisFetchError(
                f"KOSIS row #{index} is not a JSON object"
            )
        typed_rows.append(row)
    return typed_rows


def _validate_aggregate_payload(payload: dict[str, Any]) -> None:
    """Reject any payload that violates the 시군구 aggregate-only floor.

    The validator inspects two surfaces:

    1. The top-level ``aggregation_level`` field, when present.
    2. Every row in ``rows``: if a row carries an ``aggregation_level``
       field it must be in :data:`_ALLOWED_AGGREGATION_LEVELS`, otherwise
       its ``population`` denominator must be at least
       :data:`_MIN_ROW_POPULATION`.
    """

    if not isinstance(payload, dict):
        raise KosisFetchError("KOSIS payload is not a JSON object")

    top_level = payload.get("aggregation_level")
    if isinstance(top_level, str):
        if top_level in _FORBIDDEN_AGGREGATION_LEVELS:
            raise KosisAggregateOnlyError(
                f"KOSIS payload aggregation_level={top_level!r} violates "
                "the 시군구 aggregate-only floor"
            )
        if top_level not in _ALLOWED_AGGREGATION_LEVELS:
            raise KosisAggregateOnlyError(
                f"KOSIS payload aggregation_level={top_level!r} is not one "
                f"of {sorted(_ALLOWED_AGGREGATION_LEVELS)}"
            )

    for row in _iter_rows(payload):
        row_level = row.get("aggregation_level")
        if isinstance(row_level, str):
            if row_level in _FORBIDDEN_AGGREGATION_LEVELS:
                raise KosisAggregateOnlyError(
                    f"KOSIS row aggregation_level={row_level!r} violates "
                    "the 시군구 aggregate-only floor"
                )
            if row_level not in _ALLOWED_AGGREGATION_LEVELS:
                raise KosisAggregateOnlyError(
                    f"KOSIS row aggregation_level={row_level!r} is not one "
                    f"of {sorted(_ALLOWED_AGGREGATION_LEVELS)}"
                )
            continue

        # When the row has no explicit aggregation_level, the population
        # denominator becomes the only floor signal. Reject the row if
        # the population field is missing entirely OR carries a string
        # / NaN / boolean placeholder so a malicious payload cannot
        # silently cross the validator by omitting both fields.
        if "population" not in row:
            raise KosisAggregateOnlyError(
                "KOSIS row has neither aggregation_level nor population; "
                "cannot verify the 시군구 aggregate-only floor"
            )
        population = row["population"]
        if isinstance(population, bool) or not isinstance(
            population, (int, float)
        ):
            raise KosisAggregateOnlyError(
                f"KOSIS row population={population!r} is not a real number; "
                "string / boolean populations are rejected because they "
                "cannot be compared against the aggregate-only floor"
            )
        pop_float = float(population)
        if not math.isfinite(pop_float):
            raise KosisAggregateOnlyError(
                f"KOSIS row population={population!r} is not finite "
                "(NaN/Inf); aggregate-only floor cannot apply"
            )
        if pop_float < _MIN_ROW_POPULATION:
            raise KosisAggregateOnlyError(
                f"KOSIS row population={population!r} below "
                f"{_MIN_ROW_POPULATION}; treated as sub-시군구 microdata"
            )


__all__ = [
    "DEFAULT_CACHE_DIR",
    "KosisAggregateOnlyError",
    "KosisFetchClient",
    "KosisFetchError",
]
