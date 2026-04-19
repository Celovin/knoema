from __future__ import annotations

import importlib
import json
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


def test_subtask15_build_app_exposes_mirofish_inspired_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    mirofish_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "mirofish-lab-panel"
    )
    seed_prompt = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "seed-prompt-input"
    )
    event_injections = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "event-injections-input"
    )
    initial_relationships = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "initial-relationships-input"
    )
    report_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "report-agent-panel"
    )
    compare_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "compare-panel"
    )
    interview_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "interview-panel"
    )

    assert mirofish_panel.label == playground_app.LABELS["ko"]["mirofish_panel"]
    assert seed_prompt.label == playground_app.LABELS["ko"]["seed_prompt"]
    assert event_injections.label == playground_app.LABELS["ko"]["event_injections"]
    assert initial_relationships.label == playground_app.LABELS["ko"]["initial_relationships"]
    assert report_panel.label == playground_app.LABELS["ko"]["report_agent_panel"]
    assert compare_panel.label == playground_app.LABELS["ko"]["compare_panel"]
    assert interview_panel.label == playground_app.LABELS["ko"]["interview_panel"]


def test_subtask15_seed_prompt_updates_are_deterministic() -> None:
    outputs = playground_app._seed_prompt_updates(
        "crowded harbor tavern with three NPCs",
        "English",
    )

    expected_length = playground_simulation.AGENT_EDITOR_SLOT_COUNT * (
        3 + len(playground_simulation.PERSONA_TRAIT_FIELDS)
    ) + 2
    assert len(outputs) == expected_length
    assert outputs[-2]["value"].startswith("agent_1 | agent_2 |")
    assert outputs[-1].startswith("### Seed output")

    suggestions_a = playground_simulation.seed_persona_suggestions(
        "crowded harbor tavern with three NPCs",
        language="en",
    )
    suggestions_b = playground_simulation.seed_persona_suggestions(
        "crowded harbor tavern with three NPCs",
        language="en",
    )

    assert suggestions_a == suggestions_b
    assert len(suggestions_a) == playground_simulation.AGENT_EDITOR_SLOT_COUNT


def test_subtask15_run_applies_initial_relationships_and_event_injection() -> None:
    trait_defaults = {
        field_name: playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    }

    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Mina",
        primary_age=24,
        openness=trait_defaults["openness"],
        conscientiousness=trait_defaults["conscientiousness"],
        extraversion=trait_defaults["extraversion"],
        agreeableness=trait_defaults["agreeableness"],
        neuroticism=trait_defaults["neuroticism"],
        personality_overrides=trait_defaults,
        ticks=1,
        agent_count=2,
        language="en",
        event_injections_text="0 | Campus Dormitory | Fire alarm rings | agent_1,agent_2 | alarm",
        initial_relationships_text="agent_1 | agent_2 | colleague | 0.55 | 0.70 | 0.30",
    )

    assert any(
        row["relationship_type"] == "colleague" and float(row["trust"]) >= 0.7
        for row in result.relationship_rows
    )

    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert any("Fire alarm rings" in row["action"]["content"] for row in rows)


def test_subtask15_report_interview_and_compare_helpers_stay_grounded() -> None:
    jsonl_text = "\n".join(
        [
            json.dumps(
                {
                    "tick": 0,
                    "agent_id": "agent_1",
                    "action": {
                        "action_type": "speak",
                        "target": "agent_2",
                        "content": "Bjorn, stay calm.",
                    },
                }
            ),
            json.dumps(
                {
                    "tick": 0,
                    "agent_id": "agent_2",
                    "action": {
                        "action_type": "observe",
                        "target": None,
                        "content": "Bjorn studies the doorway.",
                    },
                }
            ),
        ]
    )
    memory_snapshot = {
        "agent_1": {
            "short_term": [{"content": "The courier looked nervous."}],
            "long_term": [{"content": "Bjorn usually trusts Mina."}],
            "monologue": [{"content": "Keep the room steady before the panic spreads."}],
        }
    }

    report = playground_app._report_agent_answer(
        "Who dominated the run?",
        jsonl_text,
        "Mode: Replay only | Agents: 2",
        "English",
    )
    interview = playground_app._interview_agent_answer(
        "agent_1",
        "What are you prioritizing?",
        jsonl_text,
        memory_snapshot,
        "English",
    )
    comparison = playground_app._comparison_markdown(
        SimpleNamespace(
            log_count=2,
            relationship_rows=[{"source": "agent_1", "target": "agent_2"}],
            action_breakdown={"agent_1": {"speak": 1}, "agent_2": {"observe": 1}},
        ),
        SimpleNamespace(
            log_count=3,
            relationship_rows=[{"source": "agent_1", "target": "agent_2"}] * 2,
            action_breakdown={"agent_1": {"observe": 2}, "agent_2": {"speak": 1}},
        ),
        20260419,
        20260420,
        "English",
    )

    assert "Most active agent: agent_1" in report
    assert "Dominant action: speak" in report
    assert "Recent actions: speak: Bjorn, stay calm." in interview
    assert "Inner monologue: Keep the room steady before the panic spreads." in interview
    assert "| seed | 20260419 | 20260420 |" in comparison
    assert "| relationship edges | 1 | 2 |" in comparison
