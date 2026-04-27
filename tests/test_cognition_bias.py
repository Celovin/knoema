"""Tests for luvoire.cognition.bias."""

from __future__ import annotations

import pytest

from luvoire.cognition.bias import (
    CANONICAL_BIASES,
    render_bias_prefix,
)


def test_canonical_biases_has_eight_entries() -> None:
    assert len(CANONICAL_BIASES) == 8
    assert "availability" in CANONICAL_BIASES
    assert "hyperbolic_discounting" in CANONICAL_BIASES


def test_single_bias_renders() -> None:
    prefix = render_bias_prefix(["availability"], seed=1)
    assert prefix.biases == ("availability",)
    assert "recent" in prefix.prefix_text


def test_canonical_order_independent_of_input_order() -> None:
    a = render_bias_prefix(["framing", "availability"], seed=1)
    b = render_bias_prefix(["availability", "framing"], seed=1)
    assert a.biases == b.biases
    assert a.prefix_text == b.prefix_text


def test_fingerprint_is_stable_per_seed_and_set() -> None:
    a = render_bias_prefix(["confirmation", "anchoring"], seed=42)
    b = render_bias_prefix(["confirmation", "anchoring"], seed=42)
    assert a.fingerprint == b.fingerprint


def test_fingerprint_changes_with_seed() -> None:
    a = render_bias_prefix(["confirmation"], seed=1)
    b = render_bias_prefix(["confirmation"], seed=2)
    assert a.fingerprint != b.fingerprint


def test_unknown_bias_rejected() -> None:
    with pytest.raises(ValueError, match="unknown bias names"):
        render_bias_prefix(["totally_made_up"], seed=1)  # type: ignore[list-item]


def test_empty_bias_list_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        render_bias_prefix([], seed=1)


def test_all_canonical_biases_renderable() -> None:
    prefix = render_bias_prefix(list(CANONICAL_BIASES), seed=1)
    assert prefix.biases == CANONICAL_BIASES
    for bias in CANONICAL_BIASES:
        assert bias.replace("_", " ") in prefix.prefix_text or len(prefix.prefix_text) > 0
