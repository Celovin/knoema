"""Tests for luvoire.shock.scheduler — projecting shocks onto RAT inputs."""

from __future__ import annotations

import pytest

from luvoire.shock.catalog import Catalog, Shock
from luvoire.shock.scheduler import ShockScheduler


def _shock(**overrides: object) -> Shock:
    base: dict[str, object] = {
        "shock_id": "shk",
        "kind": "festival",
        "start_tick": 0,
        "end_tick": 10,
        "affected_cells": ("synthetic-grid-r0c0",),
        "magnitude": 0.2,
        "description": "",
    }
    base.update(overrides)
    return Shock(**base)  # type: ignore[arg-type]


def test_scheduler_passes_through_when_catalog_is_empty() -> None:
    sched = ShockScheduler(Catalog())
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.5, tick=0) == 0.5
    assert sched.apply_to_guardianship("synthetic-grid-r0c0", 0.5, tick=0) == 0.5


def test_festival_increases_target_exposure() -> None:
    cat = Catalog().add(_shock(kind="festival", magnitude=0.3))
    sched = ShockScheduler(cat)
    assert sched.apply_to_target(
        "synthetic-grid-r0c0", 0.4, tick=1
    ) == pytest.approx(0.7)


def test_protest_increases_target_exposure() -> None:
    cat = Catalog().add(_shock(kind="protest", magnitude=0.25))
    sched = ShockScheduler(cat)
    assert sched.apply_to_target(
        "synthetic-grid-r0c0", 0.5, tick=1
    ) == pytest.approx(0.75)


def test_weather_event_decreases_target_exposure() -> None:
    cat = Catalog().add(_shock(kind="weather_event", magnitude=0.4))
    sched = ShockScheduler(cat)
    assert sched.apply_to_target(
        "synthetic-grid-r0c0", 0.6, tick=1
    ) == pytest.approx(0.2)


def test_apply_to_target_clamps_above_one() -> None:
    cat = Catalog().add(_shock(kind="festival", magnitude=0.9))
    sched = ShockScheduler(cat)
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.8, tick=1) == 1.0


def test_apply_to_target_clamps_below_zero() -> None:
    cat = Catalog().add(_shock(kind="weather_event", magnitude=0.9))
    sched = ShockScheduler(cat)
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.2, tick=1) == 0.0


def test_apply_to_target_skips_inactive_ticks() -> None:
    cat = Catalog().add(
        _shock(kind="festival", magnitude=0.5, start_tick=2, end_tick=4)
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.3, tick=1) == 0.3
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.3, tick=5) == 0.3
    assert sched.apply_to_target(
        "synthetic-grid-r0c0", 0.3, tick=3
    ) == pytest.approx(0.8)


def test_apply_to_target_skips_unaffected_cells() -> None:
    cat = Catalog().add(
        _shock(
            kind="festival",
            magnitude=0.5,
            affected_cells=("synthetic-grid-r0c0",),
        )
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_target("synthetic-grid-r1c1", 0.3, tick=1) == 0.3


def test_infrastructure_change_reduces_guardianship_gap() -> None:
    cat = Catalog().add(
        _shock(kind="infrastructure_change", magnitude=-0.4)
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_guardianship(
        "synthetic-grid-r0c0", 0.6, tick=1
    ) == pytest.approx(0.2)


def test_policy_change_applies_signed_magnitude_to_gap() -> None:
    closing = Catalog().add(_shock(kind="policy_change", magnitude=-0.2))
    opening = Catalog().add(_shock(kind="policy_change", magnitude=0.3))
    closing_sched = ShockScheduler(closing)
    opening_sched = ShockScheduler(opening)
    assert closing_sched.apply_to_guardianship(
        "synthetic-grid-r0c0", 0.5, tick=0
    ) == pytest.approx(0.3)
    assert opening_sched.apply_to_guardianship(
        "synthetic-grid-r0c0", 0.5, tick=0
    ) == pytest.approx(0.8)


def test_apply_to_guardianship_clamps_to_unit_interval() -> None:
    too_low = Catalog().add(
        _shock(kind="infrastructure_change", magnitude=-0.9)
    )
    too_high = Catalog().add(_shock(kind="policy_change", magnitude=0.9))
    assert (
        ShockScheduler(too_low).apply_to_guardianship(
            "synthetic-grid-r0c0", 0.2, tick=0
        )
        == 0.0
    )
    assert (
        ShockScheduler(too_high).apply_to_guardianship(
            "synthetic-grid-r0c0", 0.5, tick=0
        )
        == 1.0
    )


def test_target_apis_ignore_guardianship_only_kinds() -> None:
    cat = (
        Catalog()
        .add(_shock(kind="infrastructure_change", magnitude=-0.4))
        .add(_shock(kind="policy_change", magnitude=0.4))
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_target("synthetic-grid-r0c0", 0.5, tick=1) == 0.5


def test_guardianship_apis_ignore_target_only_kinds() -> None:
    cat = (
        Catalog()
        .add(_shock(kind="festival", magnitude=0.4))
        .add(_shock(kind="weather_event", magnitude=0.4))
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_guardianship("synthetic-grid-r0c0", 0.5, tick=1) == 0.5


def test_scheduler_accumulates_multiple_active_shocks() -> None:
    cat = (
        Catalog()
        .add(_shock(shock_id="a", kind="festival", magnitude=0.2))
        .add(_shock(shock_id="b", kind="protest", magnitude=0.1))
    )
    sched = ShockScheduler(cat)
    assert sched.apply_to_target(
        "synthetic-grid-r0c0", 0.3, tick=1
    ) == pytest.approx(0.6)


def test_scheduler_exposes_catalog() -> None:
    cat = Catalog().add(_shock())
    sched = ShockScheduler(cat)
    assert sched.catalog is cat
