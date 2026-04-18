"""Persona Consistency Score helpers."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

_AGENT_TOKEN = re.compile(r"\b(?:villager|metro|agent)[-_]?\d+\b", re.IGNORECASE)
_NON_WORD = re.compile(r"[^a-z\s]+")


def compute_pcs(simulation_log: Sequence[Mapping[str, Any]], agent_id: str) -> float:
    """Compute a heuristic Persona Consistency Score in the unit interval."""

    entries = [entry for entry in simulation_log if str(entry.get("agent_id")) == agent_id]
    if not entries:
        raise ValueError("simulation_log does not contain entries for the requested agent")
    total = len(entries)
    unique_actions = len({str(entry["action"]["action_type"]) for entry in entries})
    unique_locations = len({str(entry["action"]["location"]) for entry in entries})
    normalized_contents = {_normalize_content(str(entry["action"]["content"])) for entry in entries}
    targets = [
        str(entry["action"]["target"])
        for entry in entries
        if entry["action"].get("target") not in {None, ""}
    ]

    action_repeat = 1.0 - ((unique_actions - 1) / total)
    location_repeat = 1.0 - ((unique_locations - 1) / total)
    content_repeat = 1.0 - ((len(normalized_contents) - 1) / total)
    target_focus = 1.0 if not targets else Counter(targets).most_common(1)[0][1] / len(targets)
    score = (
        0.25 * action_repeat
        + 0.25 * location_repeat
        + 0.30 * content_repeat
        + 0.20 * target_focus
    )
    return round(max(0.0, min(1.0, score)), 3)


def _normalize_content(content: str) -> str:
    lowered = _AGENT_TOKEN.sub("agent", content.lower())
    collapsed = _NON_WORD.sub(" ", lowered)
    tokens = [token for token in collapsed.split() if len(token) > 2]
    return " ".join(tokens)


__all__ = ["compute_pcs"]
