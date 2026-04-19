from __future__ import annotations

import importlib
import json
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


def test_subtask49_build_app_exposes_mini_map_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "mini-map-panel"
    )
    plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "mini-map-plot"
    )

    assert panel.label == playground_app.LABELS["ko"]["mini_map_panel"]
    assert plot.label == playground_app.LABELS["ko"]["mini_map"]


def test_subtask49_mini_map_updates_with_tick_selection() -> None:
    rows = [
        {
            "agent_id": "aria",
            "tick": 0,
            "timestamp": "2026-04-20T08:00:00",
            "action": {
                "action_type": "move",
                "target": None,
                "content": "moves",
                "location": "Seoul > Dorm > Kitchen",
            },
        },
        {
            "agent_id": "ben",
            "tick": 0,
            "timestamp": "2026-04-20T08:00:00",
            "action": {
                "action_type": "observe",
                "target": None,
                "content": "waits",
                "location": "Seoul > Dorm > Kitchen",
            },
        },
        {
            "agent_id": "aria",
            "tick": 1,
            "timestamp": "2026-04-20T09:00:00",
            "action": {
                "action_type": "move",
                "target": None,
                "content": "moves again",
                "location": "Seoul > Dorm > Hallway",
            },
        },
        {
            "agent_id": "ben",
            "tick": 1,
            "timestamp": "2026-04-20T09:00:00",
            "action": {
                "action_type": "observe",
                "target": None,
                "content": "stays",
                "location": "Seoul > Dorm > Kitchen",
            },
        },
    ]
    jsonl = "\n".join(json.dumps(row) for row in rows)

    tick_zero = playground_app._mini_map_figure(jsonl, 0, language="en")
    tick_one = playground_app._mini_map_figure(jsonl, 1, language="en")

    assert tick_zero.data[0].type == "scatter"
    assert tick_one.data[0].type == "scatter"
    assert list(tick_zero.data[0].x) != list(tick_one.data[0].x)
    assert any("Hallway" in value for value in tick_one.data[0].hovertext)


def test_subtask49_mini_map_localizes_empty_and_batch_states() -> None:
    empty_figure = playground_app._mini_map_figure("", -1, language="en")
    batch_figure = playground_app._mini_map_figure(
        json.dumps({"record_type": "batch_summary", "batch_size": 10}),
        -1,
        language="ko",
    )

    assert empty_figure.layout.annotations[0].text == playground_app.LABELS["en"]["mini_map_empty"]
    assert batch_figure.layout.annotations[0].text == playground_app.LABELS["ko"]["mini_map_batch"]
