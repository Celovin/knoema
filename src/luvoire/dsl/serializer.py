"""Serializers for Scenario DSL v1."""

from __future__ import annotations

from typing import Any

import yaml

from luvoire.dsl.scenario import Scenario


def scenario_to_dict(scenario: Scenario) -> dict[str, Any]:
    return scenario.model_dump(mode="json", exclude_none=True)


def scenario_to_yaml(scenario: Scenario) -> str:
    return yaml.safe_dump(scenario_to_dict(scenario), sort_keys=False, allow_unicode=True)


def scenario_json_schema() -> dict[str, Any]:
    return Scenario.model_json_schema()
