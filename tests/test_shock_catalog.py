"""Tests for luvoire.shock.catalog — synthetic shock records and catalogue."""

from __future__ import annotations

import pytest

from luvoire.shock.catalog import Catalog, Shock, synthetic_festival


def _make_shock(**overrides: object) -> Shock:
    base: dict[str, object] = {
        "shock_id": "shk-1",
        "kind": "festival",
        "start_tick": 0,
        "end_tick": 10,
        "affected_cells": ("synthetic-grid-r0c0",),
        "magnitude": 0.5,
        "description": "",
    }
    base.update(overrides)
    return Shock(**base)  # type: ignore[arg-type]


def test_shock_construction_validates_tick_range() -> None:
    with pytest.raises(ValueError):
        _make_shock(start_tick=10, end_tick=5)


def test_shock_construction_allows_equal_start_and_end_tick() -> None:
    shock = _make_shock(start_tick=4, end_tick=4)
    assert shock.is_active_at(4)
    assert not shock.is_active_at(3)
    assert not shock.is_active_at(5)


def test_shock_construction_rejects_empty_affected_cells() -> None:
    with pytest.raises(ValueError):
        _make_shock(affected_cells=())


def test_shock_construction_rejects_magnitude_above_range() -> None:
    with pytest.raises(ValueError):
        _make_shock(magnitude=1.5)


def test_shock_construction_rejects_magnitude_below_range() -> None:
    with pytest.raises(ValueError):
        _make_shock(magnitude=-1.5)


def test_shock_construction_accepts_magnitude_endpoints() -> None:
    assert _make_shock(magnitude=1.0).magnitude == 1.0
    assert _make_shock(magnitude=-1.0).magnitude == -1.0


def test_shock_construction_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        _make_shock(kind="earthquake")


def test_shock_is_frozen() -> None:
    shock = _make_shock()
    with pytest.raises((AttributeError, TypeError)):
        shock.magnitude = 0.1  # type: ignore[misc]


def test_catalog_add_returns_new_instance() -> None:
    empty = Catalog()
    one = empty.add(_make_shock(shock_id="a"))
    two = one.add(_make_shock(shock_id="b"))
    assert len(empty) == 0
    assert len(one) == 1
    assert len(two) == 2
    # Original catalogues are unchanged.
    assert empty.shocks == ()
    assert tuple(s.shock_id for s in one) == ("a",)


def test_catalog_active_at_includes_start_and_end_boundaries() -> None:
    cat = Catalog().add(_make_shock(start_tick=2, end_tick=4))
    assert len(cat.active_at(1)) == 0
    assert len(cat.active_at(2)) == 1
    assert len(cat.active_at(3)) == 1
    assert len(cat.active_at(4)) == 1
    assert len(cat.active_at(5)) == 0


def test_catalog_affecting_filters_by_cell() -> None:
    cat = (
        Catalog()
        .add(
            _make_shock(
                shock_id="a", affected_cells=("synthetic-grid-r0c0",)
            )
        )
        .add(
            _make_shock(
                shock_id="b", affected_cells=("synthetic-grid-r1c1",)
            )
        )
    )
    hits = cat.affecting("synthetic-grid-r0c0")
    assert tuple(s.shock_id for s in hits) == ("a",)


def test_catalog_affecting_with_tick_filters_by_window() -> None:
    cat = (
        Catalog()
        .add(
            _make_shock(
                shock_id="early",
                start_tick=0,
                end_tick=5,
                affected_cells=("synthetic-grid-r0c0",),
            )
        )
        .add(
            _make_shock(
                shock_id="late",
                start_tick=10,
                end_tick=15,
                affected_cells=("synthetic-grid-r0c0",),
            )
        )
    )
    assert tuple(
        s.shock_id for s in cat.affecting("synthetic-grid-r0c0", tick=3)
    ) == ("early",)
    assert tuple(
        s.shock_id for s in cat.affecting("synthetic-grid-r0c0", tick=12)
    ) == ("late",)
    assert cat.affecting("synthetic-grid-r0c0", tick=7) == ()


def test_catalog_to_dict_from_dict_roundtrip() -> None:
    cat = (
        Catalog()
        .add(
            _make_shock(
                shock_id="a",
                kind="protest",
                start_tick=1,
                end_tick=2,
                affected_cells=("synthetic-grid-r0c0", "synthetic-grid-r0c1"),
                magnitude=0.25,
                description="march",
            )
        )
        .add(
            _make_shock(
                shock_id="b",
                kind="weather_event",
                magnitude=-0.4,
                description="storm",
            )
        )
    )
    payload = cat.to_dict()
    rebuilt = Catalog.from_dict(payload)
    assert rebuilt == cat
    # Round-tripping again is stable.
    assert Catalog.from_dict(rebuilt.to_dict()) == cat


def test_catalog_from_dict_rejects_unknown_kind() -> None:
    payload = {
        "shocks": [
            {
                "shock_id": "x",
                "kind": "earthquake",
                "start_tick": 0,
                "end_tick": 1,
                "affected_cells": ["synthetic-grid-r0c0"],
                "magnitude": 0.1,
                "description": "",
            }
        ]
    }
    with pytest.raises(ValueError):
        Catalog.from_dict(payload)


def test_synthetic_festival_factory_produces_valid_shock() -> None:
    shock = synthetic_festival(
        start_tick=0,
        end_tick=9,
        cells=("synthetic-grid-r0c0",),
    )
    assert shock.kind == "festival"
    assert shock.magnitude == 0.5
    assert shock.is_active_at(0)
    assert shock.is_active_at(9)
    assert not shock.is_active_at(10)


def test_catalog_iteration_yields_shocks_in_insertion_order() -> None:
    a = _make_shock(shock_id="a")
    b = _make_shock(shock_id="b")
    c = _make_shock(shock_id="c")
    cat = Catalog().add(a).add(b).add(c)
    assert tuple(s.shock_id for s in cat) == ("a", "b", "c")


def test_catalog_unique_id_helpers_report_duplicates_in_sorted_order() -> None:
    cat = (
        Catalog()
        .add(_make_shock(shock_id="b"))
        .add(_make_shock(shock_id="a"))
        .add(_make_shock(shock_id="b"))
        .add(_make_shock(shock_id="c"))
        .add(_make_shock(shock_id="a"))
    )
    assert cat.duplicate_ids() == ("a", "b")
    assert cat.has_unique_ids() is False


def test_catalog_unique_id_helpers_when_all_unique() -> None:
    cat = (
        Catalog()
        .add(_make_shock(shock_id="x"))
        .add(_make_shock(shock_id="y"))
        .add(_make_shock(shock_id="z"))
    )
    assert cat.duplicate_ids() == ()
    assert cat.has_unique_ids() is True


def test_empty_catalog_has_unique_ids() -> None:
    assert Catalog().duplicate_ids() == ()
    assert Catalog().has_unique_ids() is True
