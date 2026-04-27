"""Attention budget for the cognition middleware.

Models a per-tick cap on how many information items an agent can process. In
crowded scenes, items beyond the budget are dropped deterministically by a
seeded RNG, simulating bounded attention without invoking an LLM.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class AttentionItem:
    """An information item competing for the agent's attention.

    Higher ``salience`` (in ``[0, 1]``) makes selection more likely.
    """

    item_id: str
    salience: float


@dataclass(frozen=True, slots=True)
class AttentionDecision:
    """Output of one attention-allocation pass."""

    selected_ids: tuple[str, ...]
    dropped_ids: tuple[str, ...]
    budget: int
    seed: int


def allocate_attention(
    items: Sequence[AttentionItem],
    *,
    budget: int,
    seed: int,
) -> AttentionDecision:
    """Select up to ``budget`` items via salience-weighted seeded sampling.

    Determinism: identical inputs (items in the same order, same budget,
    same seed) produce identical decisions. Items with zero salience are
    eligible only as filler when the budget exceeds nonzero candidates.

    Raises:
        ValueError: When ``budget`` is negative or any salience is outside
            ``[0, 1]``.
    """

    if budget < 0:
        raise ValueError(f"budget must be non-negative (got {budget})")
    for item in items:
        if not 0.0 <= item.salience <= 1.0:
            raise ValueError(
                f"item {item.item_id!r} salience {item.salience} outside [0, 1]"
            )
    if not items:
        return AttentionDecision(
            selected_ids=(),
            dropped_ids=(),
            budget=budget,
            seed=seed,
        )
    # All branches preserve the original ``items`` order in the returned
    # tuples so callers can rely on a stable ordering across budget regimes.
    if budget == 0:
        return AttentionDecision(
            selected_ids=(),
            dropped_ids=tuple(item.item_id for item in items),
            budget=budget,
            seed=seed,
        )
    if budget >= len(items):
        return AttentionDecision(
            selected_ids=tuple(item.item_id for item in items),
            dropped_ids=(),
            budget=budget,
            seed=seed,
        )
    rng = np.random.default_rng(seed)
    weights = np.array([max(item.salience, 1e-9) for item in items], dtype=float)
    probs = weights / weights.sum()
    indices = rng.choice(
        len(items),
        size=budget,
        replace=False,
        p=probs,
    )
    selected = sorted(int(i) for i in indices)
    selected_ids = tuple(items[i].item_id for i in selected)
    dropped_ids = tuple(
        items[i].item_id for i in range(len(items)) if i not in set(selected)
    )
    return AttentionDecision(
        selected_ids=selected_ids,
        dropped_ids=dropped_ids,
        budget=budget,
        seed=seed,
    )


__all__ = [
    "AttentionDecision",
    "AttentionItem",
    "allocate_attention",
]
