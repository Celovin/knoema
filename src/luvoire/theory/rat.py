"""Routine Activity Theory v1 — locked convergence rule.

This module implements the Cohen and Felson (1979) routine activity theory as a
synthetic spatio-temporal convergence detector. The three classical components
(motivated offender, suitable target, capable guardianship) are operationalised
as :class:`ActorState`, :class:`TargetExposure`, and :class:`GuardianshipGap`.

The convergence rule is **locked** in this code module — Scenario DSL v2 may
reference it as Tier A (``code:luvoire.theory.rat.v1``) but never override its
definition inline. Adjustable parameters (threshold, prior distributions, layer
weights) belong in Tier B/C and live in the scenario YAML.

This module emits *synthetic opportunity events*. It is not a crime predictor,
not a victimisation estimator, and never produces an individual risk score.
See ``POLICIES/civilian_use.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VERSION: Literal["v1"] = "v1"
"""Semantic version suffix matching the canonical Tier A ref
``code:luvoire.theory.rat.v1``. Must match the trailing ``vN`` of any
Scenario DSL v2 ``ref:`` that resolves into this module so the lint
tool can verify ref<->module agreement without a separate metadata
file. Bump this in lockstep with the ref suffix when introducing v2.
"""

H3CellRef = str
"""A 15-character h3 v4 hex index, or a synthetic-grid cell label."""

DEFAULT_CONVERGENCE_THRESHOLD: float = 0.125
"""Default convergence threshold (= 0.5 * 0.5 * 0.5)."""

LOCKED_EVENT_KIND: Literal["rat_v1_synthetic_opportunity"] = (
    "rat_v1_synthetic_opportunity"
)


@dataclass(frozen=True, slots=True)
class ActorState:
    """A simulated actor with non-zero motivation toward an opportunity event.

    Note:
        The classical RAT term is *motivated offender*. We use *actor state*
        in the simulation surface to reduce labeling effects on synthetic
        populations; the connection to the motivated-offender component is
        documented in the spec text and the ASC abstract.
    """

    actor_id: str
    motivation: float
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class TargetExposure:
    """Place- and time-conditional target visibility / accessibility.

    Note:
        Classical *suitable target* decomposes via VIVA (Value, Inertia,
        Visibility, Access). We collapse VIVA into a single scalar in
        ``[0, 1]`` for simplicity; future revisions may expose components.
    """

    target_id: str
    exposure: float
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class GuardianshipGap:
    """Place-level guardianship deficit at a given tick.

    Higher values indicate lower guardianship presence (i.e., a larger gap).
    Captures formal (police, CCTV) plus informal (neighbours, foot traffic)
    layers as a single synthetic scalar.
    """

    place_id: str
    gap: float
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class OpportunityEvent:
    """A synthetic opportunity event emitted when the three RAT components
    converge in the same tick and same/adjacent cell with sufficient score.

    The :attr:`kind` field is locked to a literal string so downstream
    pipelines can pin to ``rat_v1_synthetic_opportunity`` without
    inadvertently consuming events from another (future) theory module.
    """

    tick: int
    cell: H3CellRef
    actor_id: str
    target_id: str
    place_id: str
    convergence_score: float
    kind: Literal["rat_v1_synthetic_opportunity"] = LOCKED_EVENT_KIND


def opportunity_event(
    actor_state: ActorState,
    target: TargetExposure,
    guardianship: GuardianshipGap,
    tick: int,
    cell: H3CellRef,
    *,
    threshold: float = DEFAULT_CONVERGENCE_THRESHOLD,
) -> OpportunityEvent | None:
    """Detect a synthetic opportunity-event at ``(tick, cell)``.

    The function returns an :class:`OpportunityEvent` if and only if:

    1. all three inputs report the same ``tick`` as the requested ``tick``;
    2. each input cell is the same as ``cell`` or adjacent to ``cell``
       (adjacency is judged independently for each component against
       ``cell``, not pairwise between components — three components in
       three cells that are each adjacent to ``cell`` all pass);
    3. the multiplicative convergence score
       ``actor_state.motivation * target.exposure * guardianship.gap``
       reaches or exceeds ``threshold``.

    Otherwise returns ``None``.

    Note:
        The independent-against-``cell`` adjacency rule means the three
        components form a star graph centred on ``cell``, not necessarily
        a triangle. This is the synthetic spatial convergence interpretation
        adopted by RAT v1; future theory modules may impose pairwise
        adjacency or radial distance instead.
    """

    if actor_state.tick != tick or target.tick != tick or guardianship.tick != tick:
        return None
    if not _same_or_adjacent_cell(actor_state.cell, cell):
        return None
    if not _same_or_adjacent_cell(target.cell, cell):
        return None
    if not _same_or_adjacent_cell(guardianship.cell, cell):
        return None
    score = actor_state.motivation * target.exposure * guardianship.gap
    if score < threshold:
        return None
    return OpportunityEvent(
        tick=tick,
        cell=cell,
        actor_id=actor_state.actor_id,
        target_id=target.target_id,
        place_id=guardianship.place_id,
        convergence_score=score,
    )


def _same_or_adjacent_cell(a: H3CellRef, b: H3CellRef) -> bool:
    if a == b:
        return True
    if not _is_h3_v4_string(a) or not _is_h3_v4_string(b):
        return False
    try:
        import h3  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return False
    return bool(h3.are_neighbor_cells(a, b))


def _is_h3_v4_string(value: str) -> bool:
    if len(value) != 15:
        return False
    return all(ch in "0123456789abcdef" for ch in value)


__all__ = [
    "DEFAULT_CONVERGENCE_THRESHOLD",
    "LOCKED_EVENT_KIND",
    "VERSION",
    "ActorState",
    "GuardianshipGap",
    "H3CellRef",
    "OpportunityEvent",
    "TargetExposure",
    "opportunity_event",
]
