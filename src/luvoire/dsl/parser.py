"""YAML parser for Scenario DSL v1."""

from __future__ import annotations

from pathlib import Path

import yaml

from luvoire.dsl.scenario import Scenario
from luvoire.dsl.validator import validate_scenario


def load_scenario(path: str | Path, *, validate: bool = True) -> Scenario:
    scenario_path = Path(path)
    return loads_scenario(scenario_path.read_text(encoding="utf-8"), validate=validate)


def loads_scenario(text: str, *, validate: bool = True) -> Scenario:
    payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError("Scenario YAML root must be a mapping")
    scenario = Scenario.model_validate(payload)
    if validate:
        validate_scenario(scenario)
    return scenario
