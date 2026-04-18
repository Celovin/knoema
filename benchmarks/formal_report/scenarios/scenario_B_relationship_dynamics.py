"""Scenario B: relationship dynamics benchmark definition."""

from __future__ import annotations


def get_scenario() -> dict[str, object]:
    return {
        "scenario_id": "B",
        "name": "relationship_dynamics",
        "title": "Relationship Dynamics",
        "agent_count": 12,
        "turns": 160,
        "memory_facts": 34,
        "branch_points": 11,
        "complexity": 0.41,
        "description": "Agents update trust and familiarity after cooperative and adverse exchanges.",
    }
