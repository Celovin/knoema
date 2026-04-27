"""Tests for :mod:`luvoire.timeuse.markov`."""

from __future__ import annotations

import pytest

from luvoire.timeuse.markov import (
    MarkovActivitySampler,
    TransitionMatrix,
    transition_from_dict,
)
from luvoire.timeuse.priors import ACTIVITY_CODES


def _identity_rows() -> tuple[tuple[float, ...], ...]:
    rows: list[tuple[float, ...]] = []
    for i in range(len(ACTIVITY_CODES)):
        row = [0.0] * len(ACTIVITY_CODES)
        row[i] = 1.0
        rows.append(tuple(row))
    return tuple(rows)


def _uniform_rows() -> tuple[tuple[float, ...], ...]:
    n = len(ACTIVITY_CODES)
    return tuple(tuple(1.0 / n for _ in range(n)) for _ in range(n))


def _shift_payload() -> dict[str, dict[str, float]]:
    """Cyclic shift: every state transitions to the next canonical state."""

    payload: dict[str, dict[str, float]] = {}
    n = len(ACTIVITY_CODES)
    for i, code in enumerate(ACTIVITY_CODES):
        next_code = ACTIVITY_CODES[(i + 1) % n]
        payload[code] = {target: (1.0 if target == next_code else 0.0) for target in ACTIVITY_CODES}
    return payload


def test_transition_matrix_accepts_identity() -> None:
    matrix = TransitionMatrix(matrix=_identity_rows())
    assert matrix.matrix[0][0] == pytest.approx(1.0)


def test_transition_matrix_rejects_wrong_row_count() -> None:
    rows = _identity_rows()[:-1]
    with pytest.raises(ValueError, match="rows"):
        TransitionMatrix(matrix=rows)


def test_transition_matrix_rejects_wrong_column_count() -> None:
    rows = list(_identity_rows())
    rows[0] = (1.0, 0.0)  # too short
    with pytest.raises(ValueError, match="columns"):
        TransitionMatrix(matrix=tuple(rows))


def test_transition_matrix_rejects_non_stochastic_row() -> None:
    rows = list(_identity_rows())
    rows[2] = (0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0)  # sums to 1.5
    with pytest.raises(ValueError, match=r"sum to 1\.0"):
        TransitionMatrix(matrix=tuple(rows))


def test_transition_matrix_rejects_negative_entry() -> None:
    rows = list(_identity_rows())
    rows[0] = (-0.1, 1.1, 0.0, 0.0, 0.0, 0.0, 0.0)  # row sum still 1.0
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        TransitionMatrix(matrix=tuple(rows))


def test_transition_matrix_rejects_value_above_one() -> None:
    rows = list(_identity_rows())
    rows[0] = (1.2, -0.2, 0.0, 0.0, 0.0, 0.0, 0.0)  # row sum still 1.0
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        TransitionMatrix(matrix=tuple(rows))


def test_markov_sampler_walk_determinism() -> None:
    matrix = TransitionMatrix(matrix=_uniform_rows())
    s1 = MarkovActivitySampler("sleep", matrix, seed=99)
    s2 = MarkovActivitySampler("sleep", matrix, seed=99)
    assert s1.walk(100) == s2.walk(100)


def test_markov_sampler_different_seeds_diverge() -> None:
    matrix = TransitionMatrix(matrix=_uniform_rows())
    s1 = MarkovActivitySampler("sleep", matrix, seed=1)
    s2 = MarkovActivitySampler("sleep", matrix, seed=2)
    assert s1.walk(100) != s2.walk(100)


def test_markov_sampler_identity_stays_put() -> None:
    matrix = TransitionMatrix(matrix=_identity_rows())
    sampler = MarkovActivitySampler("leisure", matrix, seed=5)
    assert all(code == "leisure" for code in sampler.walk(50))


def test_markov_sampler_cyclic_shift() -> None:
    matrix = transition_from_dict(_shift_payload())
    sampler = MarkovActivitySampler("sleep", matrix, seed=0)
    walk = sampler.walk(len(ACTIVITY_CODES))
    expected = (*ACTIVITY_CODES[1:], ACTIVITY_CODES[0])
    assert walk == expected


def test_markov_sampler_step_advances_state() -> None:
    matrix = TransitionMatrix(matrix=_identity_rows())
    sampler = MarkovActivitySampler("commute", matrix, seed=0)
    assert sampler.current == "commute"
    nxt = sampler.step()
    assert nxt == "commute"
    assert sampler.current == "commute"


def test_markov_sampler_rejects_unknown_initial() -> None:
    matrix = TransitionMatrix(matrix=_uniform_rows())
    with pytest.raises(ValueError, match="initial"):
        MarkovActivitySampler("napping", matrix, seed=0)  # type: ignore[arg-type]


def test_markov_sampler_walk_zero_returns_empty() -> None:
    matrix = TransitionMatrix(matrix=_uniform_rows())
    sampler = MarkovActivitySampler("sleep", matrix, seed=0)
    assert sampler.walk(0) == ()


def test_markov_sampler_walk_rejects_negative_steps() -> None:
    matrix = TransitionMatrix(matrix=_uniform_rows())
    sampler = MarkovActivitySampler("sleep", matrix, seed=0)
    with pytest.raises(ValueError, match="non-negative"):
        sampler.walk(-1)


def test_transition_from_dict_rejects_missing_outer_key() -> None:
    payload = _shift_payload()
    del payload["sleep"]
    with pytest.raises(ValueError, match="outer keys"):
        transition_from_dict(payload)


def test_transition_from_dict_rejects_missing_inner_key() -> None:
    payload = _shift_payload()
    del payload["sleep"]["meals"]
    with pytest.raises(ValueError, match="keys"):
        transition_from_dict(payload)
