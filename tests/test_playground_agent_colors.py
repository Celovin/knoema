from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


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

    assert list(figure.data[1].text) == ordered_agents
    assert list(figure.data[1].marker.color) == [color_map[agent_id] for agent_id in ordered_agents]


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
