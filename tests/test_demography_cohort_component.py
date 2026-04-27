"""Tests for the luvoire.demography.cohort_component Tier A alias module.

The module exists so the canonical Tier A reference
``code:luvoire.demography.cohort_component.v1`` resolves to a real
importable module path. These tests verify the alias is wired
correctly and that the VERSION constant matches the ref suffix.
"""

from __future__ import annotations

import importlib

from luvoire.demography import cohort_component as cohort_component_pkg
from luvoire.demography.cohort_component import (
    DEFAULT_MAX_AGE,
    DEFAULT_SEX_RATIO_AT_BIRTH,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    VERSION,
    CohortComponentProjector,
    CohortPopulation,
    DemographicRates,
)
from luvoire.demography.projector import (
    CohortComponentProjector as ProjectorImpl,
)
from luvoire.demography.projector import (
    CohortPopulation as PopulationImpl,
)
from luvoire.demography.projector import (
    DemographicRates as RatesImpl,
)


def test_cohort_component_module_is_importable_at_canonical_path() -> None:
    """The Tier A ref ``code:luvoire.demography.cohort_component.v1``
    must resolve to a real importable module."""

    module = importlib.import_module("luvoire.demography.cohort_component")
    assert module is not None
    assert module.VERSION == "v1"


def test_cohort_component_version_matches_tier_a_ref_suffix() -> None:
    assert VERSION == "v1"


def test_cohort_component_reexports_are_alias_of_projector() -> None:
    """The alias module must re-export the same class objects as
    luvoire.demography.projector — alias, not a fork."""

    assert CohortComponentProjector is ProjectorImpl
    assert CohortPopulation is PopulationImpl
    assert DemographicRates is RatesImpl


def test_cohort_component_constants_match_projector_constants() -> None:
    from luvoire.demography import projector as projector_module

    assert DEFAULT_MAX_AGE == projector_module.DEFAULT_MAX_AGE
    assert DEFAULT_SEX_RATIO_AT_BIRTH == projector_module.DEFAULT_SEX_RATIO_AT_BIRTH
    assert REPRODUCTIVE_AGE_HI == projector_module.REPRODUCTIVE_AGE_HI
    assert REPRODUCTIVE_AGE_LO == projector_module.REPRODUCTIVE_AGE_LO


def test_cohort_component_module_exposed_in_package() -> None:
    """``from luvoire.demography import cohort_component`` is the form
    lint_dsl_v2 / external scanners use to verify the Tier A ref.
    """

    assert cohort_component_pkg.VERSION == "v1"
