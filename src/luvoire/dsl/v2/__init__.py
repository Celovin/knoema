"""Scenario DSL v2 — variable 3-tier (A/B/C) + GIS readiness + ethics extension.

v1 scenarios continue to load via :func:`load_scenario_v2` with a deprecation
warning for one release window. New scenarios should declare ``schema_version: 2.0``.
"""

from __future__ import annotations

from luvoire.dsl.v2.parameters import (
    ParameterSpec,
    TierAParam,
    TierBParam,
    TierCParam,
)
from luvoire.dsl.v2.parser import load_scenario_v2, loads_scenario_v2
from luvoire.dsl.v2.scenario import (
    EnvironmentSpecV2,
    EthicsSpecV2,
    ScenarioV2,
)
from luvoire.dsl.v2.serializer import (
    scenario_v2_json_schema,
    scenario_v2_to_dict,
    scenario_v2_to_yaml,
)
from luvoire.dsl.v2.validator import (
    ValidationIssueV2,
    collect_validation_issues_v2,
    validate_scenario_v2,
)

__all__ = [
    "EnvironmentSpecV2",
    "EthicsSpecV2",
    "ParameterSpec",
    "ScenarioV2",
    "TierAParam",
    "TierBParam",
    "TierCParam",
    "ValidationIssueV2",
    "collect_validation_issues_v2",
    "load_scenario_v2",
    "loads_scenario_v2",
    "scenario_v2_json_schema",
    "scenario_v2_to_dict",
    "scenario_v2_to_yaml",
    "validate_scenario_v2",
]
