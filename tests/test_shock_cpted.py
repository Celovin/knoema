"""Tests for luvoire.shock.cpted — synthetic CPTED interventions."""

from __future__ import annotations

import pytest

from luvoire.shock.catalog import Catalog
from luvoire.shock.cpted import (
    cpted_cctv_install,
    cpted_lighting_install,
    cpted_natural_surveillance,
)
from luvoire.shock.scheduler import ShockScheduler


def test_lighting_install_returns_well_formed_shock() -> None:
    shock = cpted_lighting_install(("synthetic-grid-r0c0",))
    assert shock.kind == "infrastructure_change"
    assert shock.affected_cells == ("synthetic-grid-r0c0",)
    assert shock.magnitude == -0.3
    assert shock.start_tick == 0
    assert shock.end_tick >= 10**9
    assert shock.is_active_at(0)


def test_cctv_install_returns_well_formed_shock() -> None:
    shock = cpted_cctv_install(("synthetic-grid-r0c0", "synthetic-grid-r0c1"))
    assert shock.kind == "infrastructure_change"
    assert shock.magnitude == -0.4
    assert shock.affects("synthetic-grid-r0c1")


def test_natural_surveillance_returns_well_formed_shock() -> None:
    shock = cpted_natural_surveillance(("synthetic-grid-r0c0",))
    assert shock.kind == "infrastructure_change"
    assert shock.magnitude == -0.2


def test_cpted_helpers_have_negative_magnitude_polarity() -> None:
    # All three CPTED helpers must reduce the guardianship gap by default
    # (negative magnitude when applied via apply_to_guardianship).
    helpers = (
        cpted_lighting_install,
        cpted_cctv_install,
        cpted_natural_surveillance,
    )
    for helper in helpers:
        shock = helper(("synthetic-grid-r0c0",))
        assert shock.magnitude < 0.0


def test_cpted_helpers_accept_custom_tick_window() -> None:
    shock = cpted_lighting_install(
        ("synthetic-grid-r0c0",),
        start_tick=5,
        end_tick=10,
    )
    assert shock.start_tick == 5
    assert shock.end_tick == 10
    assert not shock.is_active_at(4)
    assert shock.is_active_at(5)
    assert shock.is_active_at(10)
    assert not shock.is_active_at(11)


def test_cpted_helpers_accept_custom_magnitude() -> None:
    shock = cpted_cctv_install(
        ("synthetic-grid-r0c0",),
        magnitude=-0.6,
    )
    assert shock.magnitude == -0.6


def test_cpted_helper_round_trips_through_catalog_serialization() -> None:
    shock = cpted_lighting_install(
        ("synthetic-grid-r0c0", "synthetic-grid-r0c1"),
        start_tick=2,
        end_tick=12,
        magnitude=-0.35,
    )
    catalog = Catalog().add(shock)
    rebuilt = Catalog.from_dict(catalog.to_dict())
    assert rebuilt == catalog
    assert rebuilt.shocks[0].kind == "infrastructure_change"


def test_scheduler_applies_cpted_lighting_to_guardianship_gap() -> None:
    cells = ("synthetic-grid-r0c0",)
    catalog = Catalog().add(cpted_lighting_install(cells))
    sched = ShockScheduler(catalog)
    base = 0.7
    new_gap = sched.apply_to_guardianship(cells[0], base, tick=0)
    # Lighting install reduces gap by 0.3 (clamped to >= 0).
    assert new_gap < base
    assert new_gap == pytest.approx(0.4)


def test_scheduler_applies_cpted_cctv_to_guardianship_gap() -> None:
    cells = ("synthetic-grid-r0c0",)
    catalog = Catalog().add(cpted_cctv_install(cells))
    sched = ShockScheduler(catalog)
    new_gap = sched.apply_to_guardianship(cells[0], 0.6, tick=0)
    # 0.6 + (-0.4) = 0.2.
    assert new_gap == pytest.approx(0.2)


def test_scheduler_does_not_apply_cpted_to_target_exposure() -> None:
    cells = ("synthetic-grid-r0c0",)
    catalog = Catalog().add(cpted_natural_surveillance(cells))
    sched = ShockScheduler(catalog)
    assert sched.apply_to_target(cells[0], 0.5, tick=0) == 0.5
