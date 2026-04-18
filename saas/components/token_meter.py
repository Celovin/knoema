"""Token budget helpers for research experiments."""

from __future__ import annotations

from typing import Any

from saas.services.experiment_store import cost_budget


def estimate_token_budget(
    rows: list[dict[str, Any]],
    *,
    prompt_tokens_per_action: int = 220,
    completion_tokens_per_action: int = 40,
    prompt_rate_per_million: float = 1.0,
    completion_rate_per_million: float = 3.0,
) -> dict[str, Any]:
    action_count = len(rows)
    prompt_tokens = action_count * prompt_tokens_per_action
    completion_tokens = action_count * completion_tokens_per_action
    costs = cost_budget(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_rate_per_million=prompt_rate_per_million,
        completion_rate_per_million=completion_rate_per_million,
    )
    return {
        "action_count": action_count,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        **costs,
    }
