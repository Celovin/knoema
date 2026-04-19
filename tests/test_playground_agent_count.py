from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask2_resize_agent_pool_clones_last_persona_with_small_jitter() -> None:
    config = playground_simulation.load_run_config(
        playground_simulation.scenario_path("Village: ten agents")
    )

    resized = playground_simulation._resize_agent_pool(config.agents, 20)

    assert len(resized) == 20
    assert [agent.agent_id for agent in resized[:10]] == [agent.agent_id for agent in config.agents]
    assert resized[10].agent_id == "nora-11"
    assert resized[19].agent_id == "nora-20"
    assert resized[10].location_path is None

    template = config.agents[-1].personality
    clone = resized[10].personality
    deltas = [
        abs(getattr(clone, trait_name) - getattr(template, trait_name))
        for trait_name in playground_simulation.PERSONALITY_FIELDS
    ]
    assert any(delta > 0 for delta in deltas)
    assert max(deltas) <= playground_simulation.AGENT_RESIZE_JITTER + 1e-9


def test_subtask2_run_playground_scenario_supports_single_agent() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Solo Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
        agent_count=1,
    )

    assert result.agent_count == 1
    assert result.tick_count == 2
    assert result.log_count == 2
    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert len(rows) == 2
    assert all(row["agent_id"] == "mina" for row in rows)


def test_subtask2_build_app_exposes_agent_count_slider_and_scenario_reset() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    agent_count_slider = next(
        component
        for component in components
        if type(component).__name__ == "Slider"
        and getattr(component, "minimum", None) == playground_simulation.AGENT_COUNT_MIN
        and getattr(component, "maximum", None) == playground_simulation.AGENT_COUNT_MAX
    )

    assert agent_count_slider.label == playground_app.LABELS["ko"]["agents"]
    assert agent_count_slider.info == playground_app.LABELS["ko"]["agents_info"]
    assert agent_count_slider.value == 2
    assert playground_simulation.scenario_default_agent_count("Village: ten agents") == 10

    village_update = playground_app._scenario_agent_count_update("Village: ten agents")
    assert village_update["value"] == 10
