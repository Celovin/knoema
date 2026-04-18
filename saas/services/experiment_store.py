"""Experiment storage and analysis helpers for the research dashboard."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ExperimentSummary:
    name: str
    action_count: int
    agent_count: int
    tick_count: int
    relationship_edges: int
    first_timestamp: str | None
    last_timestamp: str | None


def load_experiment_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"JSONL row must be an object at line {line_number}")
        rows.append(payload)
    return rows


def summarize_experiment(rows: list[dict[str, Any]], *, name: str = "experiment") -> ExperimentSummary:
    agents = {str(row["agent_id"]) for row in rows}
    ticks = {int(row["tick"]) for row in rows}
    edges = _relationship_edges(rows)
    timestamps = [str(row["timestamp"]) for row in rows]
    return ExperimentSummary(
        name=name,
        action_count=len(rows),
        agent_count=len(agents),
        tick_count=len(ticks),
        relationship_edges=len(edges),
        first_timestamp=timestamps[0] if timestamps else None,
        last_timestamp=timestamps[-1] if timestamps else None,
    )


def compare_experiments(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    *,
    left_name: str = "A",
    right_name: str = "B",
) -> dict[str, Any]:
    left_summary = summarize_experiment(left, name=left_name)
    right_summary = summarize_experiment(right, name=right_name)
    left_agents = {str(row["agent_id"]) for row in left}
    right_agents = {str(row["agent_id"]) for row in right}
    return {
        "left": left_summary,
        "right": right_summary,
        "action_delta": right_summary.action_count - left_summary.action_count,
        "relationship_delta": right_summary.relationship_edges - left_summary.relationship_edges,
        "shared_agents": sorted(left_agents & right_agents),
        "left_only_agents": sorted(left_agents - right_agents),
        "right_only_agents": sorted(right_agents - left_agents),
    }


def memory_inspector_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tick": row["tick"],
            "agent_id": row["agent_id"],
            "memory_proxy": row["action"]["content"],
            "target": row["action"].get("target"),
        }
        for row in rows
    ]


def relationship_graph_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter(_relationship_edges(rows))
    return [
        {"source": source, "target": target, "interactions": count}
        for (source, target), count in sorted(counter.items())
    ]


def cost_budget(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    prompt_rate_per_million: float,
    completion_rate_per_million: float,
) -> dict[str, float]:
    prompt_cost = prompt_tokens / 1_000_000 * prompt_rate_per_million
    completion_cost = completion_tokens / 1_000_000 * completion_rate_per_million
    return {
        "prompt_cost": round(prompt_cost, 6),
        "completion_cost": round(completion_cost, 6),
        "total_cost": round(prompt_cost + completion_cost, 6),
    }


def citation_bundle(*, title: str, author: str = "Celovin", year: int = 2026) -> dict[str, str]:
    key = "".join(character.lower() for character in title if character.isalnum())[:24]
    bibtex = "\n".join(
        [
            f"@software{{{key},",
            f"  author = {{{author}}},",
            f"  title = {{{title}}},",
            f"  year = {{{year}}},",
            "  url = {https://github.com/Celovin/knoema}",
            "}",
        ]
    )
    return {
        "bibtex": bibtex,
        "apa": f"{author}. ({year}). {title}. GitHub.",
    }


def _relationship_edges(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for row in rows:
        target = row["action"].get("target")
        if target is None:
            continue
        edges.append((str(row["agent_id"]), str(target)))
    return edges
