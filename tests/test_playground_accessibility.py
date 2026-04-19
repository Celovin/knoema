from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

from plotly.colors import qualitative

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask53_build_app_exposes_accessibility_ids() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    summary = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "run-summary"
    )
    graph = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "relationship-graph"
    )

    assert summary.label == playground_app.LABELS["ko"]["summary"]
    assert graph.label == playground_app.LABELS["ko"]["graph"]


def test_subtask53_head_includes_graph_accessibility_bindings() -> None:
    assert "MutationObserver" in playground_app.APP_HEAD
    assert "aria-describedby" in playground_app.APP_HEAD
    assert "run-summary" in playground_app.APP_HEAD
    assert "relationship-graph" in playground_app.APP_HEAD


def test_subtask53_uses_color_blind_safe_palettes() -> None:
    assert playground_app.AGENT_COLOR_SEQUENCE[: len(qualitative.Safe)] == tuple(qualitative.Safe)
    assert playground_app.ACTION_FLOW_COLOR_SEQUENCE[: len(qualitative.Safe)] == tuple(qualitative.Safe)


def test_subtask53_render_outputs_append_graph_text_fallback() -> None:
    result = SimpleNamespace(
        agent_count=2,
        tick_count=3,
        log_count=5,
        action_breakdown={"agent_1": {"speak": 2}},
        memory_snapshot={"agent_1": {"short_term": [], "long_term": [], "monologue": []}},
        relationship_rows=[
            {
                "source": "agent_1",
                "target": "agent_2",
                "relationship_type": "peer",
                "weight": 0.6,
                "trust": 0.8,
                "familiarity": 0.4,
            }
        ],
        jsonl="",
        timeline_markdown="",
        monologue_markdown="",
        plan_markdown="",
        download_path="",
        batch_result=None,
    )

    outputs = playground_app._render_result_outputs(
        result,
        mode_label="Replay only",
        provider="Replay only",
        api_key="",
        language="en",
    )

    assert len(outputs) == len(playground_app._noop_run_outputs())
    assert "Graph summary:" in outputs[7]
    assert "strongest link agent_1 -> agent_2" in outputs[7]
