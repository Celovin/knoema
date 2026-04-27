"""Tests for luvoire.demography.region — 시군구 string label registry."""

from __future__ import annotations

import pytest

from luvoire.demography.region import (
    REGISTERED_REGIONS,
    RegionLabel,
    lookup_region,
    regions_by_sido,
)


def test_region_label_construction_validates_admin_code_length() -> None:
    with pytest.raises(ValueError, match="5-character"):
        RegionLabel(admin_code="123", sido="서울특별시", sigungu="강남구")


def test_region_label_rejects_non_digit_admin_code() -> None:
    with pytest.raises(ValueError, match="ASCII digits"):
        RegionLabel(admin_code="ABCDE", sido="서울특별시", sigungu="강남구")


def test_region_label_rejects_empty_sido() -> None:
    with pytest.raises(ValueError, match="sido"):
        RegionLabel(admin_code="11680", sido="", sigungu="강남구")


def test_region_label_full_label_concatenates_sido_and_sigungu() -> None:
    region = RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구")
    assert region.full_label == "서울특별시 강남구"


def test_region_label_collapses_when_sido_equals_sigungu() -> None:
    region = RegionLabel(
        admin_code="36110",
        sido="세종특별자치시",
        sigungu="세종특별자치시",
    )
    assert region.full_label == "세종특별자치시"


def test_region_label_to_dict_contains_only_string_fields() -> None:
    region = RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구")
    payload = region.to_dict()
    assert set(payload.keys()) == {"admin_code", "sido", "sigungu", "full_label"}
    for value in payload.values():
        assert isinstance(value, str)


def test_region_label_dataclass_has_no_coordinate_fields() -> None:
    """Regression — RegionLabel must NEVER expose coordinate / polygon /
    EPSG / geometry fields. The aggregate-only / no-real-geometry guarantee
    of Scenario DSL v2 depends on this exclusion.
    """

    region = RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구")
    forbidden = {
        "lat", "lon", "latitude", "longitude",
        "x", "y",
        "epsg", "geometry", "polygon", "centroid",
        "bbox", "geojson", "wkt", "wkb",
    }
    for attr in forbidden:
        assert not hasattr(region, attr), (
            f"RegionLabel must not expose coordinate field {attr!r} — "
            "this would violate ethics.no_real_geometry: true"
        )


def test_registered_regions_cover_at_least_one_sido() -> None:
    assert len(REGISTERED_REGIONS) >= 1
    sidos = {r.sido for r in REGISTERED_REGIONS}
    assert "서울특별시" in sidos


def test_registered_regions_all_unique_admin_codes() -> None:
    codes = [r.admin_code for r in REGISTERED_REGIONS]
    assert len(codes) == len(set(codes))


def test_lookup_region_by_admin_code() -> None:
    region = lookup_region(admin_code="11680")
    assert region is not None
    assert region.sigungu == "강남구"


def test_lookup_region_by_full_label() -> None:
    region = lookup_region(full_label="서울특별시 강남구")
    assert region is not None
    assert region.admin_code == "11680"


def test_lookup_region_returns_none_on_miss() -> None:
    assert lookup_region(admin_code="99999") is None
    assert lookup_region(full_label="없는 지역") is None


def test_lookup_region_rejects_neither_or_both_args() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        lookup_region()
    with pytest.raises(ValueError, match="exactly one"):
        lookup_region(admin_code="11680", full_label="서울특별시 강남구")


def test_regions_by_sido_filters_correctly() -> None:
    seoul_regions = regions_by_sido("서울특별시")
    assert len(seoul_regions) >= 1
    for region in seoul_regions:
        assert region.sido == "서울특별시"


def test_regions_by_sido_rejects_empty_sido() -> None:
    with pytest.raises(ValueError, match="sido"):
        regions_by_sido("")


def test_region_label_is_frozen() -> None:
    region = RegionLabel(admin_code="11680", sido="서울특별시", sigungu="강남구")
    with pytest.raises(AttributeError):
        region.admin_code = "99999"  # type: ignore[misc]
