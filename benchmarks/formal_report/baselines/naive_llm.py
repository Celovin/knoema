"""Naive full-context LLM baseline estimates for the formal benchmark."""

from __future__ import annotations


def estimate_prompt_tokens(*, turns: int, memory_facts: int, agent_count: int, multiplier: float) -> int:
    return int(turns * (420 + memory_facts * 22 + agent_count * 8) * multiplier)


def estimate_completion_tokens(*, turns: int, multiplier: float) -> int:
    return int(turns * 42 * multiplier)


def recall_score(*, complexity: float, profile_bonus: float) -> float:
    return round(max(0.0, min(1.0, 0.49 + profile_bonus * 0.65 - complexity * 0.05)), 3)


def branching_rate(*, branch_points: int, turns: int, profile_bonus: float) -> float:
    base = branch_points * 100 / turns
    return round(base * (0.82 + profile_bonus * 0.70), 3)
