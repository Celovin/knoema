"""Dual-process (Sys 1 / Sys 2) router for the cognition middleware layer.

The router decides whether an agent's tick should resolve via a fast,
deterministic habit lookup (Sys 1) or escalate to the LLM gateway (Sys 2).
This module implements the routing decision *only* — actual habit lookups
and LLM calls are owned by callers.

The decision is itself deterministic: same agent state plus same trigger
conditions produce the same routing label. No LLM call is made by this
module; it only emits a :class:`RoutingDecision` that callers consume.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

RouteLabel = Literal["sys1_habit", "sys2_reflect"]


@dataclass(frozen=True, slots=True)
class TriggerSignal:
    """A single signal that may push the agent toward Sys-2 reflection."""

    name: str
    weight: float


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Output of the dual-process router."""

    route: RouteLabel
    score: float
    threshold: float
    triggered_by: tuple[str, ...]


def route_decision(
    triggers: Sequence[TriggerSignal],
    *,
    threshold: float = 0.5,
) -> RoutingDecision:
    """Decide between Sys-1 habit and Sys-2 reflection.

    The score is the sum of trigger weights, clipped to ``[0, 1]``. When the
    score reaches or exceeds ``threshold``, the route is ``sys2_reflect``;
    otherwise ``sys1_habit``.

    Raises:
        ValueError: When ``threshold`` is outside ``[0, 1]`` or any trigger
            weight is negative.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be in [0, 1] (got {threshold})")
    raw = 0.0
    triggered: list[str] = []
    for signal in triggers:
        if signal.weight < 0.0:
            raise ValueError(
                f"trigger {signal.name!r} has negative weight {signal.weight}"
            )
        raw += signal.weight
        if signal.weight > 0.0:
            triggered.append(signal.name)
    score = min(1.0, raw)
    if score >= threshold:
        return RoutingDecision(
            route="sys2_reflect",
            score=score,
            threshold=threshold,
            triggered_by=tuple(triggered),
        )
    return RoutingDecision(
        route="sys1_habit",
        score=score,
        threshold=threshold,
        triggered_by=tuple(triggered),
    )


__all__ = [
    "RouteLabel",
    "RoutingDecision",
    "TriggerSignal",
    "route_decision",
]
