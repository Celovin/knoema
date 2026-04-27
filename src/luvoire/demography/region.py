"""시군구 administrative-region label registry — opaque strings only.

This module deliberately stores Korean 시군구 (city / county / district)
labels as **opaque strings** plus a stable 5-digit administrative code,
*never* as coordinates, EPSG values, or polygon geometry. Storing only
labels lets demographic projections and policy what-if scenarios reference
real Korean administrative units without violating the
``ethics.no_real_geometry: true`` guardrail of Scenario DSL v2.

Registry scope
--------------
The bundled registry covers a small canonical sample (4 시군구 across
2 시도) sufficient for tests and reference. Real production scenarios
are expected to load their region set from a separate JSON fixture or
KOSIS download stub. The key invariant — ``no_coordinates``, ``no_polygon``,
``aggregation_floor='시군구'`` — is enforced at construction.

License note: 행정안전부 `행정표준코드관리시스템` distributes the
administrative-code list under KOGL Type 1; the codes themselves are not
copyrightable. We do not bundle any coordinate / geometry data here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegionLabel:
    """An opaque administrative region identifier.

    Attributes:
        admin_code: 5-digit 행정자치부 시군구 administrative code
            (e.g. ``"11680"`` for 서울특별시 강남구). Stored as a string
            because leading zeros are significant.
        sido: 시도 name in Korean (e.g. ``"서울특별시"``).
        sigungu: 시군구 name in Korean (e.g. ``"강남구"``). For 세종특별
            자치시 this duplicates :attr:`sido`.
        full_label: ``"{sido} {sigungu}"`` — the canonical human-readable
            label used as the ``region_label`` field on
            :class:`luvoire.demography.projector.CohortPopulation`.

    Construction validates that admin_code is exactly 5 ASCII digits and
    that sido / sigungu are non-empty strings. **No coordinate, polygon,
    centroid, EPSG, GeoJSON, or geographic bounding-box field is permitted**
    on this class — that is the whole point of the registry.
    """

    admin_code: str
    sido: str
    sigungu: str

    def __post_init__(self) -> None:
        if not isinstance(self.admin_code, str) or len(self.admin_code) != 5:
            raise ValueError(
                f"admin_code must be a 5-character string (got {self.admin_code!r})"
            )
        if not self.admin_code.isdigit():
            raise ValueError(
                f"admin_code must be 5 ASCII digits (got {self.admin_code!r})"
            )
        if not isinstance(self.sido, str) or not self.sido:
            raise ValueError("sido must be a non-empty string")
        if not isinstance(self.sigungu, str) or not self.sigungu:
            raise ValueError("sigungu must be a non-empty string")

    @property
    def full_label(self) -> str:
        if self.sido == self.sigungu:
            # 세종특별자치시 case — collapse to a single label.
            return self.sido
        return f"{self.sido} {self.sigungu}"

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-friendly dict — strings only, no geometry fields."""

        return {
            "admin_code": self.admin_code,
            "sido": self.sido,
            "sigungu": self.sigungu,
            "full_label": self.full_label,
        }


REGISTERED_REGIONS: tuple[RegionLabel, ...] = (
    RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구"),
    RegionLabel(admin_code="11530", sido="서울특별시", sigungu="구로구"),
    RegionLabel(admin_code="26110", sido="부산광역시", sigungu="중구"),
    RegionLabel(admin_code="36110", sido="세종특별자치시", sigungu="세종특별자치시"),
)
"""Canonical sample of 시군구 region labels used by demography tests and
reference scenarios. Production scenarios may load larger sets from JSON
fixtures, but the same construction-time geometry exclusion still applies.
"""


_BY_CODE: dict[str, RegionLabel] = {r.admin_code: r for r in REGISTERED_REGIONS}
_BY_LABEL: dict[str, RegionLabel] = {r.full_label: r for r in REGISTERED_REGIONS}


def lookup_region(*, admin_code: str | None = None, full_label: str | None = None) -> RegionLabel | None:
    """Return the registered :class:`RegionLabel` matching ``admin_code`` or
    ``full_label``.

    Exactly one of the two arguments must be provided. Returns ``None``
    when no registered region matches.
    """

    if (admin_code is None) == (full_label is None):
        raise ValueError("provide exactly one of admin_code or full_label")
    if admin_code is not None:
        if not isinstance(admin_code, str):
            raise TypeError("admin_code must be a string")
        return _BY_CODE.get(admin_code)
    assert full_label is not None  # for the type checker
    if not isinstance(full_label, str):
        raise TypeError("full_label must be a string")
    return _BY_LABEL.get(full_label)


def regions_by_sido(sido: str) -> tuple[RegionLabel, ...]:
    """Return all registered regions belonging to the given 시도."""

    if not isinstance(sido, str) or not sido:
        raise ValueError("sido must be a non-empty string")
    return tuple(r for r in REGISTERED_REGIONS if r.sido == sido)


__all__ = [
    "REGISTERED_REGIONS",
    "RegionLabel",
    "lookup_region",
    "regions_by_sido",
]
