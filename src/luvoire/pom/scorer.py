"""Composite Pattern-Oriented Modeling score.

The composite POM score collapses an iterable of :class:`GateResult` into a
single ``[0.0, 1.0]`` score plus a boolean ``all_gates_passed`` flag. The
score is defined so that "higher is better":

    composite_score = 1 - (sum_i w_i * d_i) / (sum_i w_i)

where ``d_i`` is the KS distance for gate ``i`` and ``w_i`` is its weight.
A score of ``1.0`` therefore means every gate matched its target exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

from luvoire.pom.gates import GateResult


@dataclass(frozen=True, slots=True)
class PomScore:
    """Composite POM score across a tuple of gate results."""

    gate_results: tuple[GateResult, ...]
    composite_score: float
    all_gates_passed: bool


def score_pom(results: tuple[GateResult, ...]) -> PomScore:
    """Aggregate ``results`` into a :class:`PomScore`.

    The composite score is the weight-normalised mean KS distance subtracted
    from ``1.0``. ``all_gates_passed`` is the conjunction of the individual
    gate ``passed`` flags. An empty ``results`` tuple raises ``ValueError``;
    the POM convention is that "no gates" is a configuration error rather
    than a trivial pass.
    """

    if not results:
        raise ValueError("score_pom requires at least one GateResult")

    total_weight = 0.0
    weighted_distance = 0.0
    all_passed = True
    for result in results:
        if result.weight <= 0.0:
            raise ValueError(
                f"GateResult.weight must be positive (got {result.weight} "
                f"for {result.pattern_id})"
            )
        total_weight += result.weight
        weighted_distance += result.weight * result.ks_distance
        all_passed = all_passed and result.passed

    mean_distance = weighted_distance / total_weight
    composite = 1.0 - mean_distance
    # Clamp to [0.0, 1.0] to absorb floating-point drift; KS distance is
    # already bounded in [0.0, 1.0] by construction.
    if composite < 0.0:
        composite = 0.0
    elif composite > 1.0:
        composite = 1.0
    return PomScore(
        gate_results=tuple(results),
        composite_score=float(composite),
        all_gates_passed=bool(all_passed),
    )


__all__ = [
    "PomScore",
    "score_pom",
]
