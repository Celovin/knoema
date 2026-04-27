"""Tier A canonical alias for the cohort-component projector.

Scenario DSL v2 Tier A references take the form
``code:<module>.<name>.vN`` and resolve to a module path. This module
exists so the canonical reference ``code:luvoire.demography.cohort_component.v1``
points at a real, importable module. The actual implementation lives in
:mod:`luvoire.demography.projector`; this module re-exports the public
classes under a stable namespace so future revisions can move
implementation details without breaking committed scenario YAML files.

The version suffix (``v1``) on the Tier A ref string is informational —
locking the rule version is enforced by:

- the ``VERSION`` constant below (read by lint tooling that wants to
  cross-check the ref string against the module's reported version),
- the committed test
  ``tests/test_demographic_kostat_reference.py::test_demographic_method_tier_a_locked``,
- the replay-equality CI gate (``scripts/replay_equality_ci.py``) which
  re-runs scenarios using this projector and asserts byte-identical
  ``summary_sha256`` values.
"""

from __future__ import annotations

from luvoire.demography.projector import (
    DEFAULT_MAX_AGE,
    DEFAULT_SEX_RATIO_AT_BIRTH,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortComponentProjector,
    CohortPopulation,
    DemographicRates,
    Sex,
)

VERSION: str = "v1"
"""Version tag matching the Tier A ``code:...v1`` reference suffix."""

__all__ = [
    "DEFAULT_MAX_AGE",
    "DEFAULT_SEX_RATIO_AT_BIRTH",
    "REPRODUCTIVE_AGE_HI",
    "REPRODUCTIVE_AGE_LO",
    "VERSION",
    "CohortComponentProjector",
    "CohortPopulation",
    "DemographicRates",
    "Sex",
]
