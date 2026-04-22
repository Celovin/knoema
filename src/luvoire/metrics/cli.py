"""CLI helpers for PCS and RCS scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from luvoire.metrics.persona_consistency import compute_pcs
from luvoire.metrics.relationship_coherence import compute_rcs


def score_log(log_path: str | Path) -> dict[str, Any]:
    path = Path(log_path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("log file must not be empty")
    agent_ids = sorted({str(row["agent_id"]) for row in rows})
    pcs_scores = {
        agent_id: compute_pcs(rows, agent_id)
        for agent_id in agent_ids
    }
    interacting_pairs = sorted(
        {
            tuple(sorted((str(row["agent_id"]), str(row["action"]["target"]))))
            for row in rows
            if row["action"].get("target") not in {None, ""}
        }
    )
    rcs_scores = {
        f"{left}|{right}": compute_rcs(rows, left, right)
        for left, right in interacting_pairs
    }
    pcs_values = list(pcs_scores.values())
    rcs_values = list(rcs_scores.values())
    return {
        "log_path": str(path),
        "agent_count": len(agent_ids),
        "pcs": {
            "average": round(sum(pcs_values) / len(pcs_values), 3),
            "min": round(min(pcs_values), 3),
            "max": round(max(pcs_values), 3),
            "per_agent": pcs_scores,
        },
        "rcs": {
            "average": round(sum(rcs_values) / len(rcs_values), 3) if rcs_values else 0.0,
            "pair_count": len(rcs_scores),
            "sample": dict(list(rcs_scores.items())[:10]),
        },
    }


__all__ = ["score_log"]
