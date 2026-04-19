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


def test_subtask7_agent_editor_defaults_disable_third_slot_for_two_agents() -> None:
    defaults = playground_simulation.agent_editor_defaults(
        "Dorm: two agents",
        agent_count=2,
    )

    assert len(defaults) == 3
    assert defaults[0]["enabled"] is True
    assert defaults[1]["enabled"] is True
    assert defaults[2]["enabled"] is False


def test_subtask7_agent_editor_defaults_keep_first_three_slots_for_large_runs() -> None:
    defaults = playground_simulation.agent_editor_defaults(
        "Village: ten agents",
        agent_count=10,
    )

    assert len(defaults) == 3
    assert all(default["enabled"] is True for default in defaults)
    assert defaults[2]["name"] == "Clio"


def test_subtask7_build_app_renders_three_agent_tabs() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    tabs = {
        getattr(component, "elem_id", None): component
        for component in components
        if type(component).__name__ == "Tab"
    }
    tab_three_note = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "agent-3-disabled-note"
    )

    assert "agent-tab-1" in tabs
    assert "agent-tab-2" in tabs
    assert "agent-tab-3" in tabs
    assert tabs["agent-tab-3"].interactive is False
    assert tab_three_note.visible is True


def test_subtask7_run_passes_three_agent_overrides_to_simulation(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_playground_scenario(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            mode="Replay only",
            relationship_rows=[],
            timeline_markdown="### Timeline",
            monologue_markdown="t0",
            plan_markdown="### Current plan",
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

    playground_app._run(
        "Village: ten agents",
        "university_dorm_evening",
        "",
        "Replay only",
        "",
        "",
        "Agent One",
        24,
        *trait_values,
        "Agent Two",
        29,
        *[min(1.0, value + 0.1) for value in trait_values],
        "Agent Three",
        34,
        *[max(0.0, value - 0.1) for value in trait_values],
        True,
        3,
        2,
        10,
        "English",
    )

    agent_overrides = captured["agent_overrides"]
    assert isinstance(agent_overrides, list)
    assert len(agent_overrides) == 3
    assert agent_overrides[0]["name"] == "Agent One"
    assert agent_overrides[0]["planning"] is True
    assert agent_overrides[1]["name"] == "Agent Two"
    assert agent_overrides[2]["name"] == "Agent Three"
