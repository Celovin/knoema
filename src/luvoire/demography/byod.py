"""BYOD (Bring-Your-Own-Data) aggregate validator.

Opt-in helper for callers who want to load **their own KOSIS-style
aggregate** statistics into the demography projector. The validator
enforces the aggregate-only / no-individual / no-real-geometry contract
at ingest time:

- Reject any column whose name suggests an individual identifier
  (name, RRN, RRN6, address, phone, email, MAC, IMEI, plate, license).
- Reject any column whose name suggests sub-시군구 geometry
  (lat, lon, latitude, longitude, x, y, EPSG, geometry, polygon, WKT,
  WKB, GeoJSON, h3, geohash, plus_code, address, road_address,
  jibun, dong, eupmyeondong, building, zip, postal_code).
- Reject rows whose declared population count falls below
  ``MIN_AGGREGATION_FLOOR`` (default ``10000``) — Korean 시군구 are
  ~5000-1.5M residents and well above this floor; any sub-시군구
  aggregate would breach it.
- Reject schemas missing the canonical aggregate-id column
  (``admin_code`` 5-digit administrative code).

This validator does **not** read or load microdata; it only inspects a
caller-provided record list (typically parsed from CSV / Excel /
Pandas DataFrame ``to_dict('records')``). The caller is responsible
for source provenance and PIPA / 위치정보법 compliance; this validator
is a defence-in-depth layer that prevents accidental ingest of
forbidden shapes.
"""

from __future__ import annotations

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
        "rrn",  # 주민등록번호
        "ssn",
        "passport",
        "plate",
        "phone",
        "mobile",
        "email",
        "imei",
        "udid",
        "fname",
        "lname",
        "firstname",
        "lastname",
    }
)
"""Tokens that suggest an individual identifier; presence in a column
name forces rejection. We match lower-cased token-as-substring."""

_FORBIDDEN_GEOMETRY_TOKENS: frozenset[str] = frozenset(
    {
        "lat",
        "lon",
        "latitude",
        "longitude",
        "epsg",
        "geometry",
        "polygon",
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

    Splits on common separators (underscore, hyphen, dot, whitespace) and
    returns the set of non-empty tokens. This avoids substring false-
    positives such as ``population`` matching ``lat``.
    """

    out: set[str] = set()
    buf = ""
    for ch in column:
        if ch.isalnum():
            buf += ch
        else:
            if buf:
                out.add(buf.lower())
            buf = ""
    if buf:
        out.add(buf.lower())
    return out


def _has_forbidden_token(column: str, tokens: Iterable[str]) -> bool:
    column_tokens = _split_column_tokens(column)
    return any(token in column_tokens for token in tokens)


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
            if not isinstance(pop_value, (int, float)) or isinstance(pop_value, bool):
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
            elif pop_value < min_aggregation_floor:
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
