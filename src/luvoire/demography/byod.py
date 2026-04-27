"""BYOD (Bring-Your-Own-Data) aggregate validator.

Opt-in helper for callers who want to load **their own KOSIS-style
aggregate** statistics into the demography projector. The validator
enforces the aggregate-only / no-individual / no-real-geometry contract
at ingest time:

- Reject any column whose name suggests an individual identifier
  (RRN, SSN, passport, plate, phone, mobile, email, MAC, IMEI, UDID,
  license, name family/given/full/first/last, address, birthdate, plus
  the Korean equivalents 주민등록번호 / 주민번호 / 전화번호 / 휴대전화 /
  이메일 / 주소 / 성명 / 이름 / 여권번호 / 운전면허번호 / 생년월일).
- Reject any column whose name suggests sub-시군구 geometry
  (lat, lon, lng, latitude, longitude, latLng, EPSG, geometry, polygon,
  centroid, bbox, WKT, WKB, GeoJSON, h3, geohash, plus_code, jibun,
  dong/eup/myeon, building number, zip / postal code, road_address,
  plus the Korean equivalents 위도 / 경도 / 좌표 / 도로명 / 도로명주소 /
  지번 / 지번주소 / 법정동 / 행정동 / 건물번호 / 우편번호).
- Reject rows whose declared population count falls below
  ``MIN_AGGREGATION_FLOOR`` (default ``10000``) — Korean 시군구 are
  ~5000-1.5M residents and well above this floor; any sub-시군구
  aggregate would breach it. NaN / ±Inf populations are also rejected
  because their comparison semantics let them sneak past a naive
  ``value < floor`` guard.
- Reject schemas missing the canonical aggregate-id column
  (``admin_code`` 5-digit administrative code).

Column-name matching is **token-based**: column names are split on both
non-alphanumeric separators (``_`` ``-`` ``.`` whitespace) and on
camelCase / PascalCase boundaries so disguised identifiers like
``RRNumber``, ``latLng``, ``passportNumber``, or ``firstName`` decompose
into their constituent tokens before matching.

This validator does **not** read or load microdata; it only inspects a
caller-provided record list (typically parsed from CSV / Excel /
Pandas DataFrame ``to_dict('records')``). The caller is responsible
for source provenance and PIPA / 위치정보법 compliance; this validator
is a defence-in-depth layer that prevents accidental ingest of
forbidden shapes.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

MIN_AGGREGATION_FLOOR: int = 10_000
"""Minimum aggregate population count per row. Korean 시군구 are
~5,000-1,500,000 residents — sub-시군구 aggregates fall below this
floor by construction.
"""

# Tokens forbidden anywhere in a column name. Lower-case match, anywhere.
_FORBIDDEN_INDIVIDUAL_TOKENS: frozenset[str] = frozenset(
    {
        # English / ASCII identifiers
        "rrn",  # 주민등록번호
        "rrnumber",
        "ssn",
        "passport",
        "passportno",
        "passportnumber",
        "plate",
        "phone",
        "phoneno",
        "phonenumber",
        "mobile",
        "mobileno",
        "email",
        "emailaddress",
        "mac",
        "macaddress",
        "imei",
        "udid",
        "license",
        "licenseno",
        "fname",
        "lname",
        "firstname",
        "lastname",
        "fullname",
        "givenname",
        "familyname",
        "address",
        "homeaddress",
        "streetaddress",
        "birthdate",
        "birthday",
        "dob",
        # Korean identifiers (KOSIS-style 데이터에서 흔함)
        "주민등록번호",
        "주민번호",
        "전화번호",
        "휴대전화",
        "휴대폰번호",
        "이메일",
        "이메일주소",
        "주소",
        "성명",
        "이름",
        "여권번호",
        "운전면허번호",
        "생년월일",
    }
)
"""Tokens that suggest an individual identifier; presence in a column
name forces rejection. We match lower-cased token-as-substring."""

_FORBIDDEN_GEOMETRY_TOKENS: frozenset[str] = frozenset(
    {
        # English / ASCII coordinates and geometry
        "lat",
        "lon",
        "lng",
        "latitude",
        "longitude",
        "latlng",
        "latlong",
        "epsg",
        "geometry",
        "polygon",
        "centroid",
        "bbox",
        "wkt",
        "wkb",
        "geojson",
        "h3",
        "geohash",
        "pluscode",
        "jibun",
        "eupmyeondong",
        "zip",
        "zipcode",
        "postal",
        "postalcode",
        "roadaddress",
        "buildingno",
        "buildingnumber",
        # Korean coordinates / addresses
        "위도",
        "경도",
        "좌표",
        "도로명",
        "도로명주소",
        "지번",
        "지번주소",
        "법정동",
        "행정동",
        "건물번호",
        "우편번호",
    }
)
"""Tokens that suggest sub-시군구 geometry / address / coordinate
information; presence in a column name forces rejection."""

REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "admin_code",
        "year",
        "population",
    }
)
"""Minimal canonical schema for BYOD aggregate ingest."""


@dataclass(frozen=True, slots=True)
class ByodValidationIssue:
    """One validation failure raised against a BYOD record set."""

    code: str
    column: str | None
    row_index: int | None
    message: str


def _normalise_column(name: str) -> str:
    return name.strip().lower()


def _split_column_tokens(column: str) -> set[str]:
    """Split a column name into lower-cased tokens for whole-word matching.

    Splits on common separators (underscore, hyphen, dot, whitespace) AND
    on camelCase / PascalCase boundaries so columns like ``RRNumber``,
    ``latLng``, ``passportNumber``, or ``firstName`` decompose into their
    constituent tokens. Korean tokens are preserved as-is (Korean script
    has no case so the camelCase split is a no-op for it). This avoids
    substring false-positives such as ``population`` matching ``lat``
    while still catching disguised identifiers.
    """

    out: set[str] = set()
    buf = ""
    prev_lower = False
    for ch in column:
        if ch.isalnum():
            # camelCase boundary: lower→upper transition starts a new token.
            if prev_lower and ch.isupper() and buf:
                out.add(buf.lower())
                buf = ""
            buf += ch
            prev_lower = ch.islower()
        else:
            if buf:
                out.add(buf.lower())
            buf = ""
            prev_lower = False
    if buf:
        out.add(buf.lower())
    return out


_CRITICAL_PREFIX_TOKENS: frozenset[str] = frozenset(
    {
        # Technical / legal acronyms unlikely to false-positive in
        # benign aggregate column names. Any column whose merged form
        # starts with one of these is rejected even if a 1-character
        # suffix has been appended (e.g. ``rrnx``, ``wkt0``,
        # ``imeino``, ``passportcode``). Common English words such as
        # ``address`` / ``phone`` / ``email`` are deliberately kept
        # off this list to avoid false-positives like ``addressbook``.
        "rrn",
        "ssn",
        "passport",
        "imei",
        "udid",
        "wkt",
        "wkb",
        "epsg",
        "geohash",
        "pluscode",
    }
)


def _has_forbidden_token(column: str, tokens: Iterable[str]) -> bool:
    """Return True when *column* matches any forbidden token.

    Matching is performed in three layers:

    1. **Split-token exact match** — column is split on separators and
       camelCase boundaries; each token is compared to the forbidden
       set.
    2. **Merged-form exact match** — the lowercased, non-alphanumeric-
       stripped concatenation is compared to the set, so compound
       tokens like ``firstname`` / ``buildingno`` / ``zipcode``
       still match even when their camelCase split decomposes into
       individually-too-broad tokens.
    3. **Critical-prefix match** — any token in
       :data:`_CRITICAL_PREFIX_TOKENS` that is a prefix of the merged
       form (or of any split token) triggers rejection. This closes
       the 1-character-suffix bypass attack (``rrnx``, ``wkt0``,
       ``imeino``) on the most sensitive PII / geometry acronyms.
    """

    column_tokens = _split_column_tokens(column)
    merged = "".join(c for c in column.lower() if c.isalnum())
    token_set = set(tokens)
    if any(token in column_tokens for token in token_set):
        return True
    if merged and merged in token_set:
        return True
    # Critical-prefix layer (defence-in-depth against suffix bypass).
    critical_active = _CRITICAL_PREFIX_TOKENS & token_set
    if critical_active:
        if any(merged.startswith(prefix) for prefix in critical_active):
            return True
        for tok in column_tokens:
            if any(tok.startswith(prefix) for prefix in critical_active):
                return True
    return False


def _is_finite_real(value: float | int) -> bool:
    """Return ``True`` when ``value`` is a finite real number.

    Rejects NaN and ±Inf so callers cannot smuggle a non-comparable
    placeholder past the aggregation-floor check (NaN comparisons are
    always ``False``, so a naive ``value < floor`` lets NaN through).
    """

    return math.isfinite(float(value))


def _is_numeric_scalar(value: object) -> bool:
    """Return ``True`` when ``value`` is an int or float, including
    ``numpy`` scalar types but excluding ``bool``.

    Pandas / numpy ingestion paths frequently produce ``numpy.int64`` /
    ``numpy.float64`` which do not satisfy ``isinstance(value, (int,
    float))`` on Python 3.13+. We accept anything whose ``__class__``
    declares numeric duck-typing via ``__index__`` or ``__float__``
    while still rejecting ``bool`` (a subclass of ``int`` we never
    want to treat as a population count).
    """

    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return (hasattr(value, "__float__") and hasattr(value, "__index__")) or hasattr(
        value, "__float__"
    )


def validate_aggregate_byod(
    records: list[Mapping[str, object]],
    *,
    min_aggregation_floor: int = MIN_AGGREGATION_FLOOR,
) -> list[ByodValidationIssue]:
    """Return all validation issues for ``records``.

    ``records`` is a list of per-row mappings (column-name -> value).
    Empty list returns ``[]`` for the schema check but produces a
    single ``empty_input`` issue at the head so callers can fail loudly.

    The validator is **case-insensitive on column names** for the
    forbidden-token checks and **strict on the required-column set**.
    """

    if min_aggregation_floor < 1:
        raise ValueError(
            f"min_aggregation_floor must be positive (got {min_aggregation_floor})"
        )

    issues: list[ByodValidationIssue] = []
    if not records:
        issues.append(
            ByodValidationIssue(
                code="empty_input",
                column=None,
                row_index=None,
                message="records list is empty",
            )
        )
        return issues

    columns = list(records[0].keys())
    normalised = {_normalise_column(c): c for c in columns}

    # Required-column presence (case-insensitive).
    for required in REQUIRED_COLUMNS:
        if required not in normalised:
            issues.append(
                ByodValidationIssue(
                    code="missing_required_column",
                    column=required,
                    row_index=None,
                    message=f"required column {required!r} is missing",
                )
            )

    # Forbidden-token columns.
    for column in columns:
        if _has_forbidden_token(column, _FORBIDDEN_INDIVIDUAL_TOKENS):
            issues.append(
                ByodValidationIssue(
                    code="forbidden_individual_column",
                    column=column,
                    row_index=None,
                    message=(
                        f"column {column!r} appears to be an individual "
                        "identifier; aggregate-only ingest forbids it"
                    ),
                )
            )
        if _has_forbidden_token(column, _FORBIDDEN_GEOMETRY_TOKENS):
            issues.append(
                ByodValidationIssue(
                    code="forbidden_geometry_column",
                    column=column,
                    row_index=None,
                    message=(
                        f"column {column!r} appears to be sub-시군구 "
                        "geometry / address; aggregate-only ingest forbids it"
                    ),
                )
            )

    # Per-row aggregate-floor check.
    pop_column = normalised.get("population")
    admin_column = normalised.get("admin_code")
    for row_index, record in enumerate(records):
        if admin_column is not None:
            admin_value = record.get(admin_column)
            if not isinstance(admin_value, str) or len(admin_value) != 5 or not admin_value.isdigit():
                issues.append(
                    ByodValidationIssue(
                        code="invalid_admin_code",
                        column=admin_column,
                        row_index=row_index,
                        message=(
                            f"admin_code must be a 5-digit string at row "
                            f"{row_index} (got {admin_value!r})"
                        ),
                    )
                )
        if pop_column is not None:
            pop_value = record.get(pop_column)
            if not _is_numeric_scalar(pop_value):
                issues.append(
                    ByodValidationIssue(
                        code="invalid_population",
                        column=pop_column,
                        row_index=row_index,
                        message=(
                            f"population must be numeric at row {row_index} "
                            f"(got {pop_value!r})"
                        ),
                    )
                )
            elif not _is_finite_real(pop_value):  # type: ignore[arg-type]
                issues.append(
                    ByodValidationIssue(
                        code="invalid_population",
                        column=pop_column,
                        row_index=row_index,
                        message=(
                            f"population must be finite (not NaN/Inf) at row "
                            f"{row_index} (got {pop_value!r})"
                        ),
                    )
                )
            elif float(pop_value) < min_aggregation_floor:  # type: ignore[arg-type]
                issues.append(
                    ByodValidationIssue(
                        code="below_aggregation_floor",
                        column=pop_column,
                        row_index=row_index,
                        message=(
                            f"population {pop_value} at row {row_index} is "
                            f"below aggregation floor {min_aggregation_floor}; "
                            "sub-시군구 aggregate is forbidden"
                        ),
                    )
                )
    return issues


def assert_aggregate_byod(
    records: list[Mapping[str, object]],
    *,
    min_aggregation_floor: int = MIN_AGGREGATION_FLOOR,
) -> None:
    """Run :func:`validate_aggregate_byod` and raise on the first issue.

    Convenience wrapper for callers who prefer hard-fail semantics.
    """

    issues = validate_aggregate_byod(
        records, min_aggregation_floor=min_aggregation_floor
    )
    if issues:
        details = "; ".join(f"{i.code}({i.column}@row={i.row_index}): {i.message}" for i in issues)
        raise ValueError(f"BYOD aggregate validation failed: {details}")


__all__ = [
    "MIN_AGGREGATION_FLOOR",
    "REQUIRED_COLUMNS",
    "ByodValidationIssue",
    "assert_aggregate_byod",
    "validate_aggregate_byod",
]
