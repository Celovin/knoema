from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask32_build_app_exposes_routine_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    routine_preset = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "routine-preset-dropdown"
    )
    routine_text = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "agent-routine-text"
    )

    assert routine_preset.label == playground_app.LABELS["ko"]["routine_preset"]
    assert len(routine_preset.choices) == 5
    assert routine_text.label == playground_app.LABELS["ko"]["routine_text"]


def test_subtask32_routine_presets_include_shopkeeper_schedule() -> None:
    choices = playground_simulation.routine_preset_choices("en")
    assert len(choices) == 5

    preset_text = playground_simulation.routine_preset_text("shopkeeper")

    assert "craft_item" in preset_text
    assert "Town" in preset_text
    assert "Tavern" in preset_text


def test_subtask32_run_passes_routine_text_through_to_simulation(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_playground_scenario(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            mode="Replay only",
            relationship_rows=[],
            timeline_markdown="### Timeline",
            monologue_markdown="t0",
            plan_markdown="### Current plan",
            action_breakdown={"agent-1": {"speak": 1}},
            memory_snapshot={
                "agent-1": {
                    "short_term": [],
                    "long_term": [],
                    "monologue": [],
                    "emotion": [],
                }
            },
            jsonl="{}",
            download_path="C:\\temp\\playground.jsonl",
            agent_count=3,
            tick_count=2,
            log_count=6,
        )

    monkeypatch.setattr(playground_app, "run_playground_scenario", fake_run_playground_scenario)

    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    ]
    routine_yaml = playground_simulation.routine_preset_text("shopkeeper")

    playground_app._run(
        "Village: ten agents",
        "university_dorm_evening",
        "",
        "Replay only",
        "",
        "",
        "Agent One",
        24,
        routine_yaml,
        *trait_values,
        "Agent Two",
        29,
        "",
        *[min(1.0, value + 0.1) for value in trait_values],
        "Agent Three",
        34,
        "",
        *[max(0.0, value - 0.1) for value in trait_values],
        True,
        3,
        2,
        10,
        "English",
    )

    agent_overrides = captured["agent_overrides"]
    assert isinstance(agent_overrides, list)
    assert agent_overrides[0]["routine_text"] == routine_yaml
    assert agent_overrides[1]["routine_text"] == ""
    assert agent_overrides[2]["routine_text"] == ""
