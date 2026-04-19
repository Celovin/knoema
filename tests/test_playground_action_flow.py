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


def test_subtask23_build_app_exposes_action_flow_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "action-flow-panel"
    )
    plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "action-flow-sankey"
    )

    assert panel.label == playground_app.LABELS["ko"]["action_flow_panel"]
    assert plot.label == playground_app.LABELS["ko"]["action_flow"]


def test_subtask23_action_flow_renders_sankey_with_self_stub_and_breakdown_tooltip() -> None:
    rows = [
        {
            "agent_id": "aria",
            "tick": 0,
            "timestamp": "2026-04-20T08:00:00",
            "action": {
                "action_type": "move",
                "target": None,
                "content": "moves to the square",
                "location": "Harbor Village > Market Square",
            },
        },
        {
            "agent_id": "aria",
            "tick": 1,
            "timestamp": "2026-04-20T09:00:00",
            "action": {
                "action_type": "speak",
                "target": "ben",
                "content": "asks for help",
                "location": "Harbor Village > Market Square",
            },
        },
        {
            "agent_id": "aria",
            "tick": 2,
            "timestamp": "2026-04-20T10:00:00",
            "action": {
                "action_type": "offer",
                "target": "ben",
                "content": "offers bread",
                "location": "Harbor Village > Market Square",
            },
        },
    ]
    jsonl = "\n".join(json.dumps(row) for row in rows)

    figure = playground_app._action_flow_figure(jsonl, language="en")
    sankey = figure.data[0]

    assert sankey.type == "sankey"
    assert any("(self)" in label for label in sankey.node.label)
    assert any(
        "speak x1" in item and "offer x1" in item
        for item in sankey.link.customdata
    )


def test_subtask23_action_flow_renders_for_village_run_and_localizes_batch_state() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Village: ten agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Flow Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )
    batch_result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Flow Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
        batch_mode=True,
        batch_runs=10,
        master_seed=20260419,
    )

    figure = playground_app._action_flow_figure(result.jsonl, language="en")
    batch_figure = playground_app._action_flow_figure(batch_result.jsonl, language="ko")

    assert figure.data[0].type == "sankey"
    assert len(figure.data[0].link.value) >= 5
    assert batch_figure.layout.annotations[0].text == playground_app.LABELS["ko"]["action_flow_batch"]
