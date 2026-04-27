"""YAML parser for Scenario DSL v2 with v1 deprecation upgrade path."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import yaml

from luvoire.dsl.v2.scenario import ScenarioV2
from luvoire.dsl.v2.validator import validate_scenario_v2


def load_scenario_v2(path: str | Path, *, validate: bool = True) -> ScenarioV2:
    scenario_path = Path(path)
    return loads_scenario_v2(
        scenario_path.read_text(encoding="utf-8"),
        validate=validate,
        source=str(scenario_path),
    )


def loads_scenario_v2(
    text: str,
    *,
    validate: bool = True,
    source: str | None = None,
) -> ScenarioV2:
    payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError("Scenario YAML root must be a mapping")
    schema_version = str(payload.get("schema_version", "1.0"))
    if schema_version == "1.0":
        warnings.warn(
            (
                f"{source or '<scenario>'}: Scenario DSL v1.0 is deprecated; "
                "migrate to v2.0. v1 scenarios are auto-upgraded for one "
                "release window."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        payload = _upgrade_v1_to_v2(payload)
    scenario = ScenarioV2.model_validate(payload)
    if validate:
        validate_scenario_v2(scenario)
    return scenario


def _upgrade_v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
    upgraded: dict[str, Any] = dict(payload)
    upgraded["schema_version"] = "2.0"
    upgraded.setdefault("parameters", {})
    ethics = dict(upgraded.get("ethics", {}))
    ethics.setdefault("no_real_geometry", True)
    upgraded["ethics"] = ethics
    return upgraded


__all__ = [
    "load_scenario_v2",
    "loads_scenario_v2",
]
