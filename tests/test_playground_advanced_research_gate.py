from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask39_build_app_hides_advanced_research_controls_by_default() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    scenario = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "scenario-dropdown"
    )
    tier_c_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "tier-c-panel"
    )
    advanced_mode = next(
        component
        for component in components
        if type(component).__name__ == "Checkbox"
        and getattr(component, "elem_id", None) == "advanced-research-mode"
    )
    advanced_ack = next(
        component
        for component in components
        if type(component).__name__ == "Checkbox"
        and getattr(component, "elem_id", None) == "advanced-research-ack"
    )

    assert "ER triage" not in scenario.choices
    assert "Prison yard (fictional)" not in scenario.choices
    assert tier_c_panel.visible is False
    assert advanced_mode.value is False
    assert advanced_ack.value is False


def test_subtask39_locked_gate_filters_sensitive_scenarios_and_resets_dark_tetrad() -> None:
    updates = playground_app._advanced_research_ui_updates(
        "ER triage",
        "English",
        False,
        False,
    )

    scenario_update = updates[0]
    status_text = updates[1]
    first_panel_update = updates[2]
    first_notice = updates[3]
    first_dark_updates = updates[4:8]

    assert "ER triage" not in scenario_update["choices"]
    assert scenario_update["value"] != "ER triage"
    assert "Advanced research mode keeps Dark Tetrad sliders" in status_text
    assert first_panel_update["visible"] is False
    assert "Advanced research mode keeps Dark Tetrad sliders" in first_notice
    assert [update["value"] for update in first_dark_updates] == [
        playground_app.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_app.DARK_TETRAD_FIELDS
    ]


def test_subtask39_unlock_reveals_sensitive_scenarios_and_dark_tetrad_panel() -> None:
    updates = playground_app._advanced_research_ui_updates(
        "ER triage",
        "English",
        True,
        True,
    )

    scenario_update = updates[0]
    status_text = updates[1]
    first_panel_update = updates[2]
    first_notice = updates[3]

    canonical_choices = [
        choice[1] if isinstance(choice, tuple) else choice
        for choice in scenario_update["choices"]
    ]
    assert "ER triage" in canonical_choices
    assert scenario_update["value"] == "ER triage"
    assert "Advanced research mode unlocked." in status_text
    assert first_panel_update["visible"] is True
    assert first_notice == playground_app.LABELS["en"]["dark_tetrad_notice"]


def test_subtask39_run_wrapper_blocks_sensitive_scenario_without_acknowledgement() -> None:
    outputs = playground_app._run_with_optional_streaming_ui(
        False,
        False,
        False,
        False,
        "ER triage",
        playground_app._default_environment_id(),
        "none",
        "Replay only",
        "",
        "seed-openai/gpt-5-mini",
        "Avery",
        29,
        "steady routine",
        *[
            playground_app.PERSONA_TRAIT_DEFAULTS[field_name]
            for field_name in playground_app.PERSONA_TRAIT_FIELDS
        ],
        "Jordan",
        31,
        "steady routine",
        *[
            playground_app.PERSONA_TRAIT_DEFAULTS[field_name]
            for field_name in playground_app.PERSONA_TRAIT_FIELDS
        ],
        "Riley",
        33,
        "steady routine",
        *[
            playground_app.PERSONA_TRAIT_DEFAULTS[field_name]
            for field_name in playground_app.PERSONA_TRAIT_FIELDS
        ],
        False,
        3,
        24,
        3,
        False,
        10,
        1234,
        "English",
        "",
        "",
    )

    materialized = list(outputs) if hasattr(outputs, "__iter__") and not isinstance(outputs, tuple) else outputs
    if isinstance(materialized, list) and len(materialized) == 1:
        materialized = materialized[0]
    assert len(materialized) == 21
    assert materialized[-1] == (
        "Sensitive fictional scenarios require Advanced research mode and IRB-style "
        "notice acknowledgement."
    )
