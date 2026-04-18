"""Scenario A: memory recall benchmark definition."""

from __future__ import annotations


def get_scenario() -> dict[str, object]:
    return {
        "scenario_id": "A",
        "name": "memory_recall",
        "title": "Memory Recall",
        "agent_count": 8,
        "turns": 120,
        "memory_facts": 42,
        "branch_points": 7,
        "complexity": 0.32,
        "description": "Agents must retrieve earlier commitments and preserve them across later turns.",
    }
