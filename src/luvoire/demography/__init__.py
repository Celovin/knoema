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

from luvoire.demography.byod import (
    MIN_AGGREGATION_FLOOR,
    REQUIRED_COLUMNS,
    ByodValidationIssue,
    assert_aggregate_byod,
    validate_aggregate_byod,
)
from luvoire.demography.counterfactual import (
    KOSTAT_REFERENCE_TRIPLE,
    CounterfactualScenarioEngine,
    RatePerturbation,
    ScenarioKind,
    ScenarioResult,
)
from luvoire.demography.dp import (
    DpBudget,
    DpMechanism,
    add_dp_noise,
    gaussian_noise_sigma,
    laplace_noise_scale,
)
from luvoire.demography.federated import (
    FederatedRequest,
    FederatedResponse,
    LocalAggregator,
    run_federated_local_only,
)
from luvoire.demography.kosis import (
    REGISTERED_KOSIS_TABLES,
    KosisDataKind,
    KosisTable,
    lookup_kosis_table,
    tables_by_kind,
)
from luvoire.demography.kosis_fetch import (
    DEFAULT_CACHE_DIR,
    KosisAggregateOnlyError,
    KosisFetchClient,
    KosisFetchError,
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
from luvoire.demography.report import (
    DEFAULT_FIRE_PER_1000_ELDERLY,
    DEFAULT_PATROL_PER_1000_TOTAL,
    DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE,
    ELDERLY_AGE_FLOOR,
    SCHOOL_AGE_HI,
    SCHOOL_AGE_LO,
    ServiceDemandCoefficients,
    ServiceDemandProjection,
    ServiceDemandReport,
    project_service_demand,
    render_demand_panel,
)
from luvoire.demography.synthesis import (
    CellPopulation,
    aggregate_cells_to_pyramid,
    cell_populations_total,
    synthesize_cell_populations,
)

__all__ = [
    "DEFAULT_CACHE_DIR",
    "DEFAULT_FIRE_PER_1000_ELDERLY",
    "DEFAULT_MAX_AGE",
    "DEFAULT_PATROL_PER_1000_TOTAL",
    "DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE",
    "DEFAULT_SEX_RATIO_AT_BIRTH",
    "ELDERLY_AGE_FLOOR",
    "KOSTAT_REFERENCE_TRIPLE",
    "MIN_AGGREGATION_FLOOR",
    "REGISTERED_KOSIS_TABLES",
    "REGISTERED_REGIONS",
    "REPRODUCTIVE_AGE_HI",
    "REPRODUCTIVE_AGE_LO",
    "REQUIRED_COLUMNS",
    "SCHOOL_AGE_HI",
    "SCHOOL_AGE_LO",
    "ByodValidationIssue",
    "CellPopulation",
    "CohortComponentProjector",
    "CohortPopulation",
    "CounterfactualScenarioEngine",
    "DemographicRates",
    "DpBudget",
    "DpMechanism",
    "FederatedRequest",
    "FederatedResponse",
    "KosisAggregateOnlyError",
    "KosisDataKind",
    "KosisFetchClient",
    "KosisFetchError",
    "KosisTable",
    "LocalAggregator",
    "RatePerturbation",
    "RegionLabel",
    "ScenarioKind",
    "ScenarioResult",
    "ServiceDemandCoefficients",
    "ServiceDemandProjection",
    "ServiceDemandReport",
    "Sex",
    "add_dp_noise",
    "aggregate_cells_to_pyramid",
    "assert_aggregate_byod",
    "cell_populations_total",
    "gaussian_noise_sigma",
    "laplace_noise_scale",
    "lookup_kosis_table",
    "lookup_region",
    "project_service_demand",
    "regions_by_sido",
    "render_demand_panel",
    "run_federated_local_only",
    "synthesize_cell_populations",
    "tables_by_kind",
    "validate_aggregate_byod",
]
