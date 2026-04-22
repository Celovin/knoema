from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from luvoire.dsl import (
    Scenario,
    collect_validation_issues,
    load_scenario,
    loads_scenario,
    scenario_to_yaml,
    validate_scenario,
)

SAMPLE_PATHS = [
    Path("examples/scenarios/01_shopkeeper_winter_crime.yaml"),
    Path("examples/scenarios/02_school_bullying_precursor.yaml"),
    Path("examples/scenarios/03_public_space_dispute.yaml"),
]


def test_phase22_dsl_files_exist() -> None:
    expected = [
        "src/luvoire/dsl/__init__.py",
        "src/luvoire/dsl/scenario.py",
        "src/luvoire/dsl/parser.py",
        "src/luvoire/dsl/validator.py",
        "src/luvoire/dsl/serializer.py",
        "schemas/scenario_v1.json",
        "docs/dsl/tutorial.md",
        "docs/dsl/reference.md",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase22_sample_scenarios_parse_validate_and_run() -> None:
    for path in SAMPLE_PATHS:
        scenario = load_scenario(path)
        simulator = scenario.to_simulator()
        logs = simulator.run(duration_days=scenario.duration_days)

        assert scenario.schema_version == "1.0"
        assert len(logs) == len(scenario.agents) * 2
        assert collect_validation_issues(scenario) == []


def test_phase22_serializer_round_trips_yaml() -> None:
    scenario = load_scenario(SAMPLE_PATHS[0])

    serialized = scenario_to_yaml(scenario)
    restored = loads_scenario(serialized)

    assert restored.model_dump(mode="json") == scenario.model_dump(mode="json")


def test_phase22_json_schema_exports_root_fields() -> None:
    schema = json.loads(Path("schemas/scenario_v1.json").read_text(encoding="utf-8"))
    properties = schema["properties"]

    assert schema["title"] == "Scenario"
    assert properties["scenario_id"]["pattern"] == "^[a-z0-9][a-z0-9_-]*$"
    assert "ethics" in properties


def test_phase22_validator_accepts_five_safe_variants() -> None:
    base = _base_payload()
    variants = []
    for index in range(5):
        payload = deepcopy(base)
        payload["scenario_id"] = f"safe_variant_{index}"
        payload["seed"] = 20260418 + index
        payload["metrics"][0]["name"] = f"coverage_{index}"
        variants.append(payload)

    for payload in variants:
        validate_scenario(Scenario.model_validate(payload))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("ethics", "fictional"), False),
        (("ethics", "no_real_people"), False),
        (("ethics", "no_prediction"), False),
        (("ethics", "no_suspect_scoring"), False),
        (("agents", 0, "synthetic"), False),
    ],
)
def test_phase22_validator_rejects_five_guardrail_violations(
    path: tuple[str, ...] | tuple[str, int, str],
    value: object,
) -> None:
    payload = _base_payload()
    _deep_set(payload, path, value)
    scenario = Scenario.model_validate(payload)

    with pytest.raises(ValueError, match="scenario validation failed"):
        validate_scenario(scenario)


def test_phase22_validator_rejects_disallowed_purpose_phrase() -> None:
    payload = _base_payload()
    payload["description"] = "Use the run to suspect score the plaza."
    scenario = Scenario.model_validate(payload)

    issues = collect_validation_issues(scenario)

    assert issues[0].code == "disallowed_purpose"


def _base_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scenario_id": "safe_variant",
        "title": "Safe Variant",
        "domain": "public_safety_research",
        "description": "Fictional replay for workflow review.",
        "seed": 20260418,
        "tick_duration_minutes": 720,
        "duration_days": 1,
        "environment": {
            "start_time": "2026-06-01T09:00:00",
            "location_path": ["Luvoire Demo World", "Scenario Lab"],
            "conditions": {"review": True},
        },
        "agents": [
            {
                "agent_id": "agent_a",
                "name": "Agent A",
                "age": 30,
                "background": "Synthetic participant.",
                "personality": {
                    "openness": 0.5,
                    "conscientiousness": 0.6,
                    "extraversion": 0.4,
                    "agreeableness": 0.7,
                    "neuroticism": 0.2,
                },
                "values": ["clarity"],
                "goals": ["record a safe replay"],
                "synthetic": True,
            }
        ],
        "events": [
            {
                "timestamp": "2026-06-01T15:00:00",
                "event_type": "review.checkpoint",
                "participants": ["agent_a"],
                "location": "Luvoire Demo World > Scenario Lab",
                "description": "Synthetic checkpoint.",
            }
        ],
        "metrics": [
            {
                "name": "coverage",
                "kind": "ratio",
                "description": "Replay coverage.",
            }
        ],
        "ethics": {
            "fictional": True,
            "no_real_people": True,
            "no_prediction": True,
            "no_suspect_scoring": True,
            "sensitive_domain": True,
            "irb_notes": "Synthetic review only.",
        },
    }


def _deep_set(payload: dict[str, object], path: tuple[str, ...] | tuple[str, int, str], value: object) -> None:
    current: object = payload
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    last = path[-1]
    if isinstance(last, int):
        current[last] = value  # type: ignore[index]
    else:
        current[last] = value  # type: ignore[index]
