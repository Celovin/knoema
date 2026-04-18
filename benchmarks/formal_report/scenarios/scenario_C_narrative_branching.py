"""Scenario C: narrative branching benchmark definition."""

from __future__ import annotations


def get_scenario() -> dict[str, object]:
    return {
        "scenario_id": "C",
        "name": "narrative_branching",
        "title": "Narrative Branching",
        "agent_count": 10,
        "turns": 180,
        "memory_facts": 28,
        "branch_points": 18,
        "complexity": 0.47,
        "description": "Agents create inspectable branch flags while retaining coherent local context.",
    }
