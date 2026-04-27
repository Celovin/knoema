"""Demographic projection subpackage — synthetic-only, aggregate-only.

This subpackage implements the cohort-component demographic projection
technique used by KOSTAT 장래인구추계 and UN World Population Prospects.
It is the long-horizon counterfactual scenario engine that informs
public-safety service-demand projections (학교·119·파출소 인프라 수요)
under different fertility / mortality / migration trajectories.

Civilian Use Policy alignment
-----------------------------
- Output is **always aggregate** at registered 시군구 region labels.
  No per-person, no sub-시군구 geometry, no individual-level prediction.
- Region labels are stored as **opaque strings**, never as coordinates,
  EPSG values, or polygon geometry — the ``ethics.no_real_geometry: true``
  guardrail of Scenario DSL v2 is preserved.
- Tier B parameters reference KOSIS aggregate tables (``KOGL Type 1``)
  via :mod:`luvoire.demography.kosis`; no microdata is bundled or loaded.
- Output trajectories are **counterfactual scenarios** (추계), not
  predictions (예측). Multiple labelled rate perturbations produce
  parallel trajectories for policy what-if comparison, in line with
  KOSTAT 저위/중위/고위 scenario practice.
"""

from luvoire.demography.counterfactual import (
    KOSTAT_REFERENCE_TRIPLE,
    CounterfactualScenarioEngine,
    RatePerturbation,
    ScenarioKind,
    ScenarioResult,
)
from luvoire.demography.kosis import (
    REGISTERED_KOSIS_TABLES,
    KosisDataKind,
    KosisTable,
    lookup_kosis_table,
    tables_by_kind,
)
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
from luvoire.demography.region import (
    REGISTERED_REGIONS,
    RegionLabel,
    lookup_region,
    regions_by_sido,
)

__all__ = [
    "DEFAULT_MAX_AGE",
    "DEFAULT_SEX_RATIO_AT_BIRTH",
    "KOSTAT_REFERENCE_TRIPLE",
    "REGISTERED_KOSIS_TABLES",
    "REGISTERED_REGIONS",
    "REPRODUCTIVE_AGE_HI",
    "REPRODUCTIVE_AGE_LO",
    "CohortComponentProjector",
    "CohortPopulation",
    "CounterfactualScenarioEngine",
    "DemographicRates",
    "KosisDataKind",
    "KosisTable",
    "RatePerturbation",
    "RegionLabel",
    "ScenarioKind",
    "ScenarioResult",
    "Sex",
    "lookup_kosis_table",
    "lookup_region",
    "regions_by_sido",
    "tables_by_kind",
]
