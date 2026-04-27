"""Tests for luvoire.theory.rat v1 — locked convergence rule."""

from __future__ import annotations

import pytest

from luvoire.theory.rat import (
    DEFAULT_CONVERGENCE_THRESHOLD,
    LOCKED_EVENT_KIND,
    ActorState,
    GuardianshipGap,
    OpportunityEvent,
    TargetExposure,
    opportunity_event,
)

CELL_A = "synthetic-grid-r3c4"
CELL_B = "synthetic-grid-r9c1"
H3_CELL = "8830e1ad81fffff"


def _trio(
    *,
    motivation: float = 0.6,
    exposure: float = 0.6,
    gap: float = 0.6,
    cell: str = CELL_A,
    tick: int = 7,
) -> tuple[ActorState, TargetExposure, GuardianshipGap]:
    return (
        ActorState(actor_id="a", motivation=motivation, cell=cell, tick=tick),
        TargetExposure(target_id="t", exposure=exposure, cell=cell, tick=tick),
        GuardianshipGap(place_id="p", gap=gap, cell=cell, tick=tick),
    )


def test_convergence_above_threshold_emits_event() -> None:
    actor, target, guardian = _trio(motivation=0.9, exposure=0.9, gap=0.9)
    event = opportunity_event(actor, target, guardian, tick=7, cell=CELL_A)
    assert isinstance(event, OpportunityEvent)
    assert event.tick == 7
    assert event.cell == CELL_A
    assert event.actor_id == "a"
    assert event.target_id == "t"
    assert event.place_id == "p"


def test_convergence_below_threshold_returns_none() -> None:
    actor, target, guardian = _trio(motivation=0.3, exposure=0.3, gap=0.3)
    assert opportunity_event(actor, target, guardian, tick=7, cell=CELL_A) is None


def test_mismatched_tick_returns_none() -> None:
    actor, target, guardian = _trio()
    actor_late = ActorState(
        actor_id="a", motivation=actor.motivation, cell=actor.cell, tick=8
    )
    assert (
        opportunity_event(actor_late, target, guardian, tick=7, cell=CELL_A) is None
    )


def test_actor_in_distant_cell_returns_none() -> None:
    actor, target, guardian = _trio()
    actor_far = ActorState(
        actor_id="a", motivation=actor.motivation, cell=CELL_B, tick=actor.tick
    )
    assert (
        opportunity_event(actor_far, target, guardian, tick=7, cell=CELL_A) is None
    )


def test_same_synthetic_cell_emits_event_when_score_clears() -> None:
    actor, target, guardian = _trio(motivation=0.7, exposure=0.7, gap=0.7)
    event = opportunity_event(actor, target, guardian, tick=7, cell=CELL_A)
    assert event is not None
    assert event.convergence_score == pytest.approx(0.7 * 0.7 * 0.7)


def test_h3_neighbor_cells_recognized_when_h3_installed() -> None:
    h3 = pytest.importorskip("h3")
    neighbors = h3.grid_disk(H3_CELL, 1)
    different = next(cell for cell in neighbors if cell != H3_CELL)
    actor, target, guardian = _trio(cell=H3_CELL, motivation=0.9, exposure=0.9, gap=0.9)
    event = opportunity_event(actor, target, guardian, tick=7, cell=different)
    assert event is not None


def test_event_contains_convergence_score() -> None:
    actor, target, guardian = _trio(motivation=0.6, exposure=0.6, gap=0.6)
    event = opportunity_event(actor, target, guardian, tick=7, cell=CELL_A)
    assert event is not None
    assert event.convergence_score == pytest.approx(0.6 * 0.6 * 0.6)


def test_event_kind_is_locked_to_rat_v1_synthetic() -> None:
    actor, target, guardian = _trio(motivation=0.9, exposure=0.9, gap=0.9)
    event = opportunity_event(actor, target, guardian, tick=7, cell=CELL_A)
    assert event is not None
    assert event.kind == "rat_v1_synthetic_opportunity"
    assert event.kind == LOCKED_EVENT_KIND


def test_threshold_default_is_one_eighth() -> None:
    assert pytest.approx(0.125) == DEFAULT_CONVERGENCE_THRESHOLD


def test_threshold_override_respected() -> None:
    actor, target, guardian = _trio(motivation=0.4, exposure=0.4, gap=0.4)
    score = 0.4 * 0.4 * 0.4
    assert opportunity_event(actor, target, guardian, tick=7, cell=CELL_A) is None
    bumped = opportunity_event(
        actor, target, guardian, tick=7, cell=CELL_A, threshold=score
    )
    assert bumped is not None


def test_event_dataclass_is_frozen_and_hashable() -> None:
    actor, target, guardian = _trio(motivation=0.9, exposure=0.9, gap=0.9)
    event = opportunity_event(actor, target, guardian, tick=7, cell=CELL_A)
    assert event is not None
    with pytest.raises((AttributeError, TypeError)):
        event.tick = 99  # type: ignore[misc]
    assert hash(event) == hash(event)


def test_input_dataclasses_are_immutable() -> None:
    actor, target, guardian = _trio()
    with pytest.raises((AttributeError, TypeError)):
        actor.motivation = 0.0  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        target.exposure = 0.0  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        guardian.gap = 0.0  # type: ignore[misc]


def test_distinct_synthetic_cells_not_adjacent() -> None:
    actor = ActorState(actor_id="a", motivation=0.9, cell=CELL_A, tick=7)
    target = TargetExposure(target_id="t", exposure=0.9, cell=CELL_B, tick=7)
    guardian = GuardianshipGap(place_id="p", gap=0.9, cell=CELL_A, tick=7)
    assert opportunity_event(actor, target, guardian, tick=7, cell=CELL_A) is None


def test_target_tick_mismatch_returns_none() -> None:
    actor, target, guardian = _trio()
    target_late = TargetExposure(
        target_id="t", exposure=target.exposure, cell=target.cell, tick=99
    )
    assert (
        opportunity_event(actor, target_late, guardian, tick=7, cell=CELL_A) is None
    )


# --- Audit-3 hardening: VERSION constant matches Tier A ref suffix -----


def test_rat_module_version_constant_is_v1() -> None:
    """Tier A ref ``code:luvoire.theory.rat.v1`` must match
    ``module.VERSION`` so the lint_dsl_v2 import-resolution check
    succeeds. Round-3 audit fix.
    """

    from luvoire.theory import rat as rat_module

    assert rat_module.VERSION == "v1"
