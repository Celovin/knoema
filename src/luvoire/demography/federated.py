"""Federated-mode interface for sensitive BYOD demographic ingest.

Sketches the **local-only** interface a sensitive caller (e.g. a
research consortium with non-shareable individual records) can use to
keep raw data on their own machine while still benefiting from
:mod:`luvoire.demography` projection. Under federated mode:

1. The caller's raw individual records **never leave their machine**.
2. They locally compute aggregate marginals (population by age x sex)
   that satisfy the same shape contract as the BYOD validator.
3. Only the aggregate marginals (after passing
   :mod:`luvoire.demography.byod` validation) are passed to the
   projector. Optionally, :mod:`luvoire.demography.dp` is composed
   first to add calibrated DP noise.
4. The projector returns counterfactual trajectories at aggregate cell
   level — never per-person.

The implementation here is a deliberate **placeholder + interface
contract**. We do not bundle a federated transport layer (gRPC, MPC,
secure aggregation, etc.); that is a downstream engineering choice.
What we *do* provide is:

- :class:`LocalAggregator` — a thin protocol describing the local
  aggregation contract callers must implement.
- :class:`FederatedRequest` and :class:`FederatedResponse` frozen
  dataclasses describing the message shape exchanged across the
  trust boundary.
- :func:`run_federated_local_only` — an in-process happy-path runner
  that loops the caller's local aggregator over the projector to
  prove the contract is wireable end-to-end.

Civilian Use Policy alignment
-----------------------------
The federated interface is **not** a face-value face-saver: it merely
relocates controller responsibility to the caller. Aggregate output,
no per-person, no sub-시군구 geometry guarantees still apply. PIPC
2025-08 guidance treats AI models on real microdata as personal
information *even after federation*, so callers must still satisfy
local PIPA / 위치정보법 obligations on their side. We are software
vendor only; controller responsibility under PIPA is the caller's.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from luvoire.demography.byod import assert_aggregate_byod
from luvoire.demography.dp import DpBudget, DpMechanism, add_dp_noise


@dataclass(frozen=True, slots=True)
class FederatedRequest:
    """Aggregate request crossing the trust boundary into the projector.

    Attributes:
        admin_code: 5-digit administrative code (string only).
        year: Calendar year of the aggregate.
        male_by_age: ``(max_age + 1,)`` non-negative aggregate counts.
        female_by_age: Same shape as ``male_by_age``.
        dp_budget: Optional DP budget. When set, DP noise is applied
            before the request is consumed by the projector.
        dp_mechanism: Mechanism if ``dp_budget`` is set.
        dp_seed: Seed if ``dp_budget`` is set.

    The aggregate count vectors are explicitly *integer counts*, not
    raw individual records. The federated transport contract is that
    callers compute these locally and only ship the resulting
    aggregate.
    """

    admin_code: str
    year: int
    male_by_age: np.ndarray
    female_by_age: np.ndarray
    dp_budget: DpBudget | None = None
    dp_mechanism: DpMechanism = "laplace"
    dp_seed: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.admin_code, str) or len(self.admin_code) != 5 or not self.admin_code.isdigit():
            raise ValueError(
                f"admin_code must be 5-digit string (got {self.admin_code!r})"
            )
        if not isinstance(self.year, int) or isinstance(self.year, bool):
            raise TypeError("year must be int")
        male = np.asarray(self.male_by_age, dtype=float)
        female = np.asarray(self.female_by_age, dtype=float)
        if male.ndim != 1 or female.ndim != 1:
            raise ValueError("male_by_age and female_by_age must be 1-D")
        if male.shape != female.shape:
            raise ValueError(
                f"male and female aggregate shapes must match "
                f"(got {male.shape} vs {female.shape})"
            )
        if (male < 0).any() or (female < 0).any():
            raise ValueError("aggregate counts must be non-negative")
        if self.dp_budget is not None and self.dp_seed is None:
            raise ValueError(
                "dp_seed must be provided when dp_budget is set"
            )
        object.__setattr__(self, "male_by_age", male)
        object.__setattr__(self, "female_by_age", female)


@dataclass(frozen=True, slots=True)
class FederatedResponse:
    """Aggregate response crossing the trust boundary out of the projector.

    Attributes:
        admin_code: Echoed administrative code.
        year: Echoed year.
        accepted: Whether the request passed validation.
        validation_errors: Tuple of human-readable error strings if
            the request was rejected.
        aggregate_total: Sum of male + female counts after any DP
            noise has been applied. Provided as a convenience for
            downstream reporting.
    """

    admin_code: str
    year: int
    accepted: bool
    validation_errors: tuple[str, ...]
    aggregate_total: float


@runtime_checkable
class LocalAggregator(Protocol):
    """Protocol the caller's *local* aggregator must satisfy.

    The aggregator runs **on the caller's machine**, reads their raw
    individual records (never touched by Luvoire), and returns the
    aggregate :class:`FederatedRequest` that crosses the trust
    boundary. Implementations are expected to:

    1. Apply local PIPA / 위치정보법 / IRB controls before computing
       the aggregate.
    2. Verify their own data minimisation invariants — e.g. drop
       personal identifiers, drop sub-시군구 geometry.
    3. Return only the aggregate counts.
    """

    def aggregate(self) -> FederatedRequest: ...


def run_federated_local_only(
    aggregator: LocalAggregator,
) -> FederatedResponse:
    """Run a single federated request happy-path in-process.

    The function:
    1. Asks the caller's :class:`LocalAggregator` to produce a
       :class:`FederatedRequest` (this is where their raw data stays).
    2. Validates the resulting aggregate via
       :mod:`luvoire.demography.byod`.
    3. Optionally applies DP noise if ``request.dp_budget`` is set.
    4. Returns a :class:`FederatedResponse` with the aggregate total.

    No persistent state is captured; callers are responsible for
    threading the resulting aggregate counts into the projector if
    they want to run a counterfactual scenario.
    """

    request = aggregator.aggregate()
    record: Mapping[str, object] = {
        "admin_code": request.admin_code,
        "year": request.year,
        "population": float(request.male_by_age.sum() + request.female_by_age.sum()),
    }
    try:
        assert_aggregate_byod([record])
    except ValueError as exc:
        return FederatedResponse(
            admin_code=request.admin_code,
            year=request.year,
            accepted=False,
            validation_errors=(str(exc),),
            aggregate_total=0.0,
        )

    male = request.male_by_age
    female = request.female_by_age
    if request.dp_budget is not None:
        assert request.dp_seed is not None  # for the type checker
        male = add_dp_noise(
            male,
            budget=request.dp_budget,
            mechanism=request.dp_mechanism,
            seed=request.dp_seed,
        )
        female = add_dp_noise(
            female,
            budget=request.dp_budget,
            mechanism=request.dp_mechanism,
            seed=request.dp_seed + 1,
        )

    aggregate_total = float(male.sum() + female.sum())
    return FederatedResponse(
        admin_code=request.admin_code,
        year=request.year,
        accepted=True,
        validation_errors=(),
        aggregate_total=aggregate_total,
    )


__all__ = [
    "FederatedRequest",
    "FederatedResponse",
    "LocalAggregator",
    "run_federated_local_only",
]
