"""Tests for luvoire.cognition.attention."""

from __future__ import annotations

import pytest

from luvoire.cognition.attention import (
    AttentionItem,
    allocate_attention,
)


def test_empty_items_returns_empty_decision() -> None:
    decision = allocate_attention([], budget=3, seed=1)
    assert decision.selected_ids == ()
    assert decision.dropped_ids == ()


def test_zero_budget_drops_all() -> None:
    items = [AttentionItem(f"i{i}", 0.5) for i in range(3)]
    decision = allocate_attention(items, budget=0, seed=1)
    assert decision.selected_ids == ()
    assert set(decision.dropped_ids) == {"i0", "i1", "i2"}


def test_budget_exceeds_items_returns_all() -> None:
    items = [AttentionItem(f"i{i}", 0.5) for i in range(2)]
    decision = allocate_attention(items, budget=5, seed=1)
    assert set(decision.selected_ids) == {"i0", "i1"}
    assert decision.dropped_ids == ()


def test_partial_budget_selects_subset() -> None:
    items = [AttentionItem(f"i{i}", 0.5) for i in range(5)]
    decision = allocate_attention(items, budget=2, seed=1)
    assert len(decision.selected_ids) == 2
    assert len(decision.dropped_ids) == 3


def test_determinism_per_seed() -> None:
    items = [AttentionItem(f"i{i}", float(i + 1) / 6) for i in range(5)]
    a = allocate_attention(items, budget=2, seed=42)
    b = allocate_attention(items, budget=2, seed=42)
    assert a.selected_ids == b.selected_ids


def test_different_seeds_diverge() -> None:
    items = [AttentionItem(f"i{i}", 0.5) for i in range(5)]
    a = allocate_attention(items, budget=2, seed=1)
    b = allocate_attention(items, budget=2, seed=2)
    assert a.selected_ids != b.selected_ids


def test_negative_budget_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        allocate_attention([], budget=-1, seed=1)


def test_salience_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="salience"):
        allocate_attention(
            [AttentionItem("bad", 1.5)], budget=1, seed=1
        )


def test_high_salience_more_likely_selected() -> None:
    items = [
        AttentionItem("low", 0.02),
        AttentionItem("high", 0.98),
    ] + [AttentionItem(f"mid_{i}", 0.05) for i in range(8)]
    selected_high = 0
    for seed in range(60):
        decision = allocate_attention(items, budget=2, seed=seed)
        if "high" in decision.selected_ids:
            selected_high += 1
    # High-salience item dominates the prob mass; expect overwhelming majority.
    assert selected_high >= 50
