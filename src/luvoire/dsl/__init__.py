"""Scenario DSL public API.

v1 (``Scenario``, ``load_scenario``) remains importable for one release window.
v2 (``ScenarioV2``, ``load_scenario_v2``) introduces the variable 3-tier (A/B/C)
parameter system, optional GIS-readiness fields, and the
``ethics.no_real_geometry`` guardrail. See :mod:`luvoire.dsl.v2`.
"""

from luvoire.dsl.parser import load_scenario, loads_scenario
from luvoire.dsl.scenario import (
    AgentSpec,
    EnvironmentSpec,
    EthicsSpec,
    EventSpec,
    MetricSpec,
    PersonalitySpec,
    Scenario,
)
from luvoire.dsl.serializer import scenario_json_schema, scenario_to_dict, scenario_to_yaml
from luvoire.dsl.v2 import (
    EnvironmentSpecV2,
    EthicsSpecV2,
    ParameterSpec,
    ScenarioV2,
    TierAParam,
    TierBParam,
    TierCParam,
    load_scenario_v2,
    loads_scenario_v2,
    scenario_v2_json_schema,
    scenario_v2_to_dict,
    scenario_v2_to_yaml,
    validate_scenario_v2,
)
from luvoire.dsl.validator import ValidationIssue, collect_validation_issues, validate_scenario

__all__ = [
    "AgentSpec",
    "EnvironmentSpec",
    "EnvironmentSpecV2",
    "EthicsSpec",
    "EthicsSpecV2",
    "EventSpec",
    "MetricSpec",
    "ParameterSpec",
    "PersonalitySpec",
    "Scenario",
    "ScenarioV2",
    "TierAParam",
    "TierBParam",
    "TierCParam",
    "ValidationIssue",
    "collect_validation_issues",
    "load_scenario",
    "load_scenario_v2",
    "loads_scenario",
    "loads_scenario_v2",
    "scenario_json_schema",
    "scenario_to_dict",
    "scenario_to_yaml",
    "scenario_v2_json_schema",
    "scenario_v2_to_dict",
    "scenario_v2_to_yaml",
    "validate_scenario",
    "validate_scenario_v2",
]
