"""시군구 administrative-region label registry — opaque strings only.

This module deliberately stores Korean 시군구 (city / county / district)
labels as **opaque strings** plus a 5-digit administrative code,
*never* as coordinates, EPSG values, or polygon geometry. Storing only
labels lets demographic projections and policy what-if scenarios
reference real Korean administrative units without violating the
``ethics.no_real_geometry: true`` guardrail of Scenario DSL v2.

Registry scope
--------------
The bundled registry covers all 17 광역 시도 (특별시·광역시·도·특별
자치도·특별자치시) with at least one 시군구 each — a canonical sample
sufficient for tests and reference. Real production scenarios are
expected to load their region set from a separate JSON fixture or
KOSIS download stub. The key invariant — ``no_coordinates``,
``no_polygon``, ``aggregation_floor='시군구'`` — is enforced at
construction.

Administrative-code provenance
------------------------------
The 5-digit codes here follow the **통계청 SGIS** 시군구 code convention
(matching the prefix scheme used across KOSIS and 통계지리정보서비스
exports). They overlap with but **are not identical to** the 행정안전
부 행정표준코드관리시스템 10-digit codes. For 강원특별자치도 (구
강원도, 명칭 변경 2023-06-11) and 전북특별자치도 (구 전라북도, 명칭
변경 2024-01-18) the SGIS codes use 51xxx / 52xxx, whereas 행정자치
부 historical codes used 42xxx / 45xxx. **Treat the codes here as
illustrative SGIS-style placeholders** — production callers should
verify against the canonical 행안부 export of their target year before
cross-referencing with KOSIS.

License note: 통계청 SGIS distributes its administrative-code list
under KOGL Type 1; the codes themselves are not copyrightable. We do
not bundle any coordinate / geometry data here.
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
    # 서울특별시 (11xxx)
    RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구"),
    RegionLabel(admin_code="11530", sido="서울특별시", sigungu="구로구"),
    # 부산광역시 (26xxx)
    RegionLabel(admin_code="26110", sido="부산광역시", sigungu="중구"),
    RegionLabel(admin_code="26350", sido="부산광역시", sigungu="해운대구"),
    # 대구광역시 (27xxx)
    RegionLabel(admin_code="27110", sido="대구광역시", sigungu="중구"),
    RegionLabel(admin_code="27200", sido="대구광역시", sigungu="동구"),
    # 인천광역시 (28xxx)
    RegionLabel(admin_code="28110", sido="인천광역시", sigungu="중구"),
    RegionLabel(admin_code="28245", sido="인천광역시", sigungu="연수구"),
    # 광주광역시 (29xxx)
    RegionLabel(admin_code="29110", sido="광주광역시", sigungu="동구"),
    RegionLabel(admin_code="29155", sido="광주광역시", sigungu="서구"),
    # 대전광역시 (30xxx)
    RegionLabel(admin_code="30110", sido="대전광역시", sigungu="동구"),
    RegionLabel(admin_code="30200", sido="대전광역시", sigungu="중구"),
    # 울산광역시 (31xxx)
    RegionLabel(admin_code="31110", sido="울산광역시", sigungu="중구"),
    RegionLabel(admin_code="31170", sido="울산광역시", sigungu="남구"),
    # 세종특별자치시 (36xxx) — sido == sigungu
    RegionLabel(admin_code="36110", sido="세종특별자치시", sigungu="세종특별자치시"),
    # 경기도 (41xxx)
    RegionLabel(admin_code="41110", sido="경기도", sigungu="수원시"),
    RegionLabel(admin_code="41130", sido="경기도", sigungu="성남시"),
    # 강원특별자치도 (51xxx) — renamed 2023
    RegionLabel(admin_code="51110", sido="강원특별자치도", sigungu="춘천시"),
    RegionLabel(admin_code="51130", sido="강원특별자치도", sigungu="원주시"),
    # 충청북도 (43xxx)
    RegionLabel(admin_code="43110", sido="충청북도", sigungu="청주시"),
    RegionLabel(admin_code="43130", sido="충청북도", sigungu="충주시"),
    # 충청남도 (44xxx)
    RegionLabel(admin_code="44130", sido="충청남도", sigungu="천안시"),
    # 전북특별자치도 (52xxx) — renamed 2024
    RegionLabel(admin_code="52110", sido="전북특별자치도", sigungu="전주시"),
    RegionLabel(admin_code="52130", sido="전북특별자치도", sigungu="군산시"),
    # 전라남도 (46xxx)
    RegionLabel(admin_code="46110", sido="전라남도", sigungu="목포시"),
    RegionLabel(admin_code="46130", sido="전라남도", sigungu="여수시"),
    # 경상북도 (47xxx)
    RegionLabel(admin_code="47110", sido="경상북도", sigungu="포항시"),
    RegionLabel(admin_code="47130", sido="경상북도", sigungu="경주시"),
    # 경상남도 (48xxx)
    RegionLabel(admin_code="48120", sido="경상남도", sigungu="창원시"),
    RegionLabel(admin_code="48250", sido="경상남도", sigungu="김해시"),
    # 제주특별자치도 (50xxx)
    RegionLabel(admin_code="50110", sido="제주특별자치도", sigungu="제주시"),
    RegionLabel(admin_code="50130", sido="제주특별자치도", sigungu="서귀포시"),
)
"""Canonical sample of 시군구 region labels used by demography tests and
reference scenarios. Covers all 17 시도 (특별시·광역시·도·특별자치도·
특별자치시) with at least one 시군구 each. Production scenarios may load
larger sets from JSON fixtures, but the same construction-time geometry
exclusion still applies.

시도 명칭 주의:
- ``강원특별자치도`` (구 강원도, 2023-06-11 명칭 변경)
- ``전북특별자치도`` (구 전라북도, 2024-01-18 명칭 변경)
- 세종특별자치시는 산하 시군구가 없어 ``sido == sigungu`` 로 표기.
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
