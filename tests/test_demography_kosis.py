"""Tests for luvoire.demography.kosis — KOSIS metadata registry."""

from __future__ import annotations

import pytest

from luvoire.demography.kosis import (
    REGISTERED_KOSIS_TABLES,
    KosisTable,
    lookup_kosis_table,
    tables_by_kind,
)


def _make_table(**overrides: object) -> KosisTable:
    base: dict[str, object] = {
        "publisher": "KOSTAT",
        "table_id": "TEST-1",
        "kind": "fertility",
        "description": "test table",
        "aggregation_floor": "시군구",
        "license": "KOGL Type 1",
    }
    base.update(overrides)
    return KosisTable(**base)  # type: ignore[arg-type]


def test_kosis_table_construction_validates_publisher() -> None:
    with pytest.raises(ValueError, match="publisher"):
        _make_table(publisher="")


def test_kosis_table_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown kind"):
        _make_table(kind="not_a_kind")


def test_kosis_table_rejects_sub_sigungu_aggregation() -> None:
    with pytest.raises(ValueError, match="sub-시군구"):
        _make_table(aggregation_floor="동")


def test_kosis_table_accepts_시도_floor() -> None:
    table = _make_table(aggregation_floor="시도")
    assert table.aggregation_floor == "시도"


def test_registered_tables_cover_five_canonical_kinds() -> None:
    assert len(REGISTERED_KOSIS_TABLES) >= 5
    kinds = {table.kind for table in REGISTERED_KOSIS_TABLES}
    assert {"fertility", "mortality", "migration", "population_pyramid", "projection"} <= kinds


def test_registered_tables_all_aggregate_floor_or_above() -> None:
    for table in REGISTERED_KOSIS_TABLES:
        assert table.aggregation_floor in {"시군구", "시도", "전국"}


def test_registered_tables_all_kogl_type1_licensed() -> None:
    for table in REGISTERED_KOSIS_TABLES:
        assert "KOGL" in table.license


def test_lookup_kosis_table_finds_canonical_fertility_id() -> None:
    table = lookup_kosis_table("KOSTAT", "1B36E27")
    assert table is not None
    assert table.kind == "fertility"


def test_lookup_kosis_table_returns_none_on_miss() -> None:
    assert lookup_kosis_table("KOSTAT", "DOES-NOT-EXIST") is None


def test_lookup_kosis_table_publisher_disambiguation() -> None:
    # Same table_id under different publisher should not match.
    assert lookup_kosis_table("MOIS", "1B36E27") is None


def test_tables_by_kind_filters_correctly() -> None:
    fertility_tables = tables_by_kind("fertility")
    assert len(fertility_tables) >= 1
    for table in fertility_tables:
        assert table.kind == "fertility"


def test_tables_by_kind_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown kind"):
        tables_by_kind("not_a_kind")  # type: ignore[arg-type]


def test_kosis_table_is_frozen() -> None:
    table = _make_table()
    with pytest.raises(AttributeError):
        table.publisher = "OTHER"  # type: ignore[misc]
