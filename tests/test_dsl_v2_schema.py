"""Schema export and root-field coverage tests for Scenario DSL v2."""

from __future__ import annotations

from luvoire.dsl.v2 import scenario_v2_json_schema


def test_schema_has_v2_title() -> None:
    schema = scenario_v2_json_schema()
    assert schema["title"] == "ScenarioV2"


def test_schema_root_required_fields() -> None:
    schema = scenario_v2_json_schema()
    required = set(schema["required"])
    assert {
        "scenario_id",
        "title",
        "domain",
        "description",
        "seed",
        "environment",
        "agents",
    }.issubset(required)


def test_schema_lists_parameters_field() -> None:
    schema = scenario_v2_json_schema()
    assert "parameters" in schema["properties"]
    parameters_field = schema["properties"]["parameters"]
    assert parameters_field["type"] == "object"


def test_schema_environment_has_h3_cell_pattern() -> None:
    schema = scenario_v2_json_schema()
    env_def = schema["$defs"]["EnvironmentSpecV2"]
    h3_field = env_def["properties"]["h3_cell"]
    any_of = h3_field.get("anyOf", [])
    assert any(option.get("pattern") == r"^[0-9a-f]{15}$" for option in any_of)


def test_schema_ethics_includes_no_real_geometry() -> None:
    schema = scenario_v2_json_schema()
    ethics_def = schema["$defs"]["EthicsSpecV2"]
    assert "no_real_geometry" in ethics_def["properties"]
    assert ethics_def["properties"]["no_real_geometry"]["default"] is True


def test_schema_ethics_includes_demographic_projection_and_pssdp_mode() -> None:
    schema = scenario_v2_json_schema()
    ethics_def = schema["$defs"]["EthicsSpecV2"]
    assert "demographic_projection" in ethics_def["properties"]
    assert ethics_def["properties"]["demographic_projection"]["default"] is False
    assert "pssdp_mode" in ethics_def["properties"]
    assert ethics_def["properties"]["pssdp_mode"]["default"] is False
