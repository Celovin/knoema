from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _relationship_traces(figure: object) -> tuple[object, list[object]]:
    node_trace = next(
        trace
        for trace in getattr(figure, "data", [])
        if getattr(trace, "type", "") == "scatter3d" and getattr(trace, "mode", "") == "markers+text"
    )
    edge_traces = [
        trace
        for trace in getattr(figure, "data", [])
        if getattr(trace, "type", "") == "scatter3d" and getattr(trace, "mode", "") == "lines"
    ]
    return node_trace, edge_traces


def test_subtask11_relationship_graph_uses_deterministic_agent_colors() -> None:
    rows = [
        {
            "source": "alice",
            "target": "bob",
            "relationship_type": "friend",
            "weight": 0.8,
            "trust": 0.7,
            "familiarity": 0.5,
        },
        {
            "source": "bob",
            "target": "cara",
            "relationship_type": "ally",
            "weight": 0.6,
            "trust": 0.8,
            "familiarity": 0.4,
        },
    ]

    figure = playground_app._relationship_figure(rows, language="en")
    ordered_agents = ["alice", "bob", "cara"]
    color_map = playground_app._agent_color_map(ordered_agents)
    node_trace, edge_traces = _relationship_traces(figure)

    assert len(edge_traces) == len(rows)
    assert list(node_trace.text) == ordered_agents
    assert list(node_trace.marker.color) == [color_map[agent_id] for agent_id in ordered_agents]


def test_subtask63_relationship_graph_uses_force_layout_and_weighted_edges() -> None:
    rows = [
        {
            "source": "alice",
            "target": "bob",
            "relationship_type": "friend",
            "weight": 0.2,
            "trust": 0.1,
            "familiarity": 0.4,
        },
        {
            "source": "alice",
            "target": "cara",
            "relationship_type": "ally",
            "weight": 0.9,
            "trust": 0.9,
            "familiarity": 0.7,
        },
        {
            "source": "bob",
            "target": "cara",
            "relationship_type": "coworker",
            "weight": 0.4,
            "trust": 0.5,
            "familiarity": 0.5,
        },
        {
            "source": "cara",
            "target": "dana",
            "relationship_type": "mentor",
            "weight": 0.7,
            "trust": 0.8,
            "familiarity": 0.6,
        },
        {
            "source": "dana",
            "target": "eli",
            "relationship_type": "neighbor",
            "weight": 0.3,
            "trust": 0.4,
            "familiarity": 0.3,
        },
        {
            "source": "cara",
            "target": "eli",
            "relationship_type": "friend",
            "weight": 1.0,
            "trust": 0.95,
            "familiarity": 0.8,
        },
    ]

    figure = playground_app._relationship_figure(rows, language="en")
    node_trace, edge_traces = _relationship_traces(figure)
    node_sizes = list(node_trace.marker.size)
    edge_widths = [float(trace.line.width) for trace in edge_traces]

    assert len(edge_traces) >= 2
    assert len(set(node_sizes)) > 1
    assert max(edge_widths) > min(edge_widths)
    assert figure.layout.scene.aspectmode == "cube"


def test_subtask11_timeline_and_memory_header_share_agent_color_map() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Color Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
    )

    agent_ids = sorted(result.memory_snapshot)
    agent_id = agent_ids[0]
    color_map = playground_app._agent_color_map(agent_ids)
    timeline = playground_app._timeline_markdown_with_agent_colors(
        result.jsonl,
        result.timeline_markdown,
        color_map,
        language="en",
    )
    memory = playground_app._memory_inspector_markdown(
        result.memory_snapshot,
        agent_id,
        language="en",
    )

    assert "●" in timeline
    assert color_map[agent_id] in timeline
    assert f"background:{color_map[agent_id]}22" in memory
    assert f"border-left:4px solid {color_map[agent_id]}" in memory
