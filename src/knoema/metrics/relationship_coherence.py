"""Relationship Coherence Score helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def compute_rcs(
    simulation_log: Sequence[Mapping[str, Any]],
    agent_a: str,
    agent_b: str,
) -> float:
    """Compute a heuristic Relationship Coherence Score in the unit interval."""

    if not agent_a.strip() or not agent_b.strip():
        raise ValueError("agent ids must not be blank")
    if agent_a == agent_b:
        return 0.0
    pair_entries = [
        entry
        for entry in simulation_log
        if _matches_pair(entry, agent_a=agent_a, agent_b=agent_b)
    ]
    if not pair_entries:
        return 0.0

    directions = {
        (str(entry.get("agent_id")), str(entry["action"].get("target")))
        for entry in pair_entries
    }
    reciprocal_score = 1.0 if len(directions) > 1 else 0.6
    location_alignment = _alignment_score(
        [str(entry["action"]["location"]) for entry in pair_entries]
    )
    action_alignment = _alignment_score(
        [str(entry["action"]["action_type"]) for entry in pair_entries]
    )
    density_score = min(1.0, len(pair_entries) / 2)
    score = (
        0.35 * reciprocal_score
        + 0.25 * location_alignment
        + 0.20 * action_alignment
        + 0.20 * density_score
    )
    return round(max(0.0, min(1.0, score)), 3)


def _matches_pair(entry: Mapping[str, Any], *, agent_a: str, agent_b: str) -> bool:
    source = str(entry.get("agent_id"))
    target = entry["action"].get("target")
    if target in {None, ""}:
        return False
    normalized_target = str(target)
    return {source, normalized_target} == {agent_a, agent_b}


def _alignment_score(values: Sequence[str]) -> float:
    unique = len(set(values))
    if unique <= 1:
        return 1.0
    return max(0.0, 1.0 - ((unique - 1) / len(values)))


__all__ = ["compute_rcs"]
