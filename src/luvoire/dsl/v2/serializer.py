"""Serializers and JSON Schema export for Scenario DSL v2."""

from __future__ import annotations

from typing import Any

import yaml

from luvoire.dsl.v2.scenario import ScenarioV2


def scenario_v2_to_dict(scenario: ScenarioV2) -> dict[str, Any]:
    return scenario.model_dump(mode="json", exclude_none=True)


def scenario_v2_to_yaml(scenario: ScenarioV2) -> str:
    return yaml.safe_dump(
        scenario_v2_to_dict(scenario),
        sort_keys=False,
        allow_unicode=True,
    )


def scenario_v2_json_schema() -> dict[str, Any]:
    return ScenarioV2.model_json_schema()


__all__ = [
    "scenario_v2_json_schema",
    "scenario_v2_to_dict",
    "scenario_v2_to_yaml",
]
