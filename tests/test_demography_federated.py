"""Tests for luvoire.demography.federated — local-only federated stub."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.demography.dp import DpBudget
from luvoire.demography.federated import (
    FederatedRequest,
    FederatedResponse,
    LocalAggregator,
    run_federated_local_only,
)


class _StubAggregator:
    """In-test stand-in for a caller's local aggregator."""

    def __init__(self, request: FederatedRequest) -> None:
        self._request = request

    def aggregate(self) -> FederatedRequest:
        return self._request


def _flat_request(
    *,
    admin_code: str = "11680",
    year: int = 2024,
    count_per_age: float = 5_000.0,
    max_age: int = 100,
    dp_budget: DpBudget | None = None,
    dp_seed: int | None = None,
) -> FederatedRequest:
    return FederatedRequest(
        admin_code=admin_code,
        year=year,
        male_by_age=np.full(max_age + 1, count_per_age),
        female_by_age=np.full(max_age + 1, count_per_age),
        dp_budget=dp_budget,
        dp_seed=dp_seed,
    )


# --- FederatedRequest ----------------------------------------------------


def test_federated_request_rejects_bad_admin_code() -> None:
    with pytest.raises(ValueError, match="admin_code"):
        FederatedRequest(
            admin_code="123",
            year=2024,
            male_by_age=np.zeros(10),
            female_by_age=np.zeros(10),
        )


def test_federated_request_rejects_2d_arrays() -> None:
    with pytest.raises(ValueError, match="1-D"):
        FederatedRequest(
            admin_code="11680",
            year=2024,
            male_by_age=np.zeros((3, 3)),
            female_by_age=np.zeros((3, 3)),
        )


def test_federated_request_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError, match="shapes must match"):
        FederatedRequest(
            admin_code="11680",
            year=2024,
            male_by_age=np.zeros(10),
            female_by_age=np.zeros(20),
        )


def test_federated_request_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        FederatedRequest(
            admin_code="11680",
            year=2024,
            male_by_age=np.array([1.0, -1.0]),
            female_by_age=np.array([1.0, 1.0]),
        )


def test_federated_request_rejects_dp_budget_without_seed() -> None:
    with pytest.raises(ValueError, match="dp_seed"):
        FederatedRequest(
            admin_code="11680",
            year=2024,
            male_by_age=np.zeros(10),
            female_by_age=np.zeros(10),
            dp_budget=DpBudget(epsilon=1.0),
        )


def test_federated_request_is_frozen() -> None:
    req = _flat_request()
    with pytest.raises(AttributeError):
        req.year = 9999  # type: ignore[misc]


# --- run_federated_local_only -------------------------------------------


def test_run_federated_local_only_accepts_valid_request() -> None:
    aggregator = _StubAggregator(_flat_request())
    response = run_federated_local_only(aggregator)
    assert response.accepted is True
    assert response.validation_errors == ()
    assert response.aggregate_total > 0


def test_run_federated_local_only_rejects_below_floor_aggregate() -> None:
    """Population total below MIN_AGGREGATION_FLOOR is rejected by
    the underlying BYOD validator."""

    aggregator = _StubAggregator(
        _flat_request(count_per_age=10.0)  # total = 2 * 101 * 10 = 2020 < 10000
    )
    response = run_federated_local_only(aggregator)
    assert response.accepted is False
    assert any("below_aggregation_floor" in e for e in response.validation_errors)


def test_run_federated_local_only_applies_dp_noise_when_budget_set() -> None:
    budget = DpBudget(epsilon=1.0, sensitivity=1.0)
    request_clean = _flat_request()
    request_noisy = _flat_request(dp_budget=budget, dp_seed=42)

    response_clean = run_federated_local_only(_StubAggregator(request_clean))
    response_noisy = run_federated_local_only(_StubAggregator(request_noisy))
    assert response_clean.accepted
    assert response_noisy.accepted
    # The aggregate totals will differ because DP noise was added.
    assert response_clean.aggregate_total != response_noisy.aggregate_total


def test_local_aggregator_protocol_is_runtime_checkable() -> None:
    aggregator = _StubAggregator(_flat_request())
    assert isinstance(aggregator, LocalAggregator)


def test_response_echoes_admin_code_and_year() -> None:
    aggregator = _StubAggregator(_flat_request(admin_code="26110", year=2025))
    response = run_federated_local_only(aggregator)
    assert response.admin_code == "26110"
    assert response.year == 2025


def test_federated_response_is_frozen() -> None:
    response = FederatedResponse(
        admin_code="11680",
        year=2024,
        accepted=True,
        validation_errors=(),
        aggregate_total=10_000.0,
    )
    with pytest.raises(AttributeError):
        response.accepted = False  # type: ignore[misc]


def test_run_federated_local_only_is_deterministic_with_dp() -> None:
    """Two runs with the same dp_seed should produce the same aggregate
    total (post-noise)."""

    request_a = _flat_request(dp_budget=DpBudget(epsilon=1.0), dp_seed=42)
    request_b = _flat_request(dp_budget=DpBudget(epsilon=1.0), dp_seed=42)
    response_a = run_federated_local_only(_StubAggregator(request_a))
    response_b = run_federated_local_only(_StubAggregator(request_b))
    assert response_a.aggregate_total == response_b.aggregate_total
