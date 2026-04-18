"""Scenario D: scalability benchmark definition."""

from __future__ import annotations


def get_scenario() -> dict[str, object]:
    return {
        "scenario_id": "D",
        "name": "scalability",
        "title": "Scalability",
        "agent_count": 50,
        "turns": 420,
        "memory_facts": 60,
        "branch_points": 22,
        "complexity": 0.58,
        "scalability_agents": [5, 10, 25, 50],
        "description": "The same policy is evaluated across larger synthetic village populations.",
    }
