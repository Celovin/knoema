from __future__ import annotations

import importlib
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from knoema import Environment, Persona, Personality, Simulator
from knoema.cognition import MonologueGenerator
from knoema.environment import EnvironmentContext

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _agent(agent_id: str, *, conscientiousness: float = 0.6) -> Persona:
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=22,
        background="Synthetic participant in a dormitory hallway.",
        personality=Personality(0.5, conscientiousness, 0.4, 0.6, 0.3),
        values=["respect"],
        goals=["keep the interaction orderly"],
    )


def _environment() -> Environment:
    return Environment(
        start_time=datetime(2026, 4, 19, 10, 0),
        location_path=("Knoema Demo World", "Seoul", "Dormitory"),
        conditions={"weather": "clear"},
    )


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_phase17_monologue_generator_replay_mode_references_dominant_trait() -> None:
    context = EnvironmentContext(
        agent_id="alice",
        timestamp=datetime(2026, 4, 19, 10, 0),
        location_path=("Knoema Demo World", "Seoul", "Dormitory"),
        conditions={"weather": "clear"},
    )

    monologue = MonologueGenerator().generate(
        _agent("alice", conscientiousness=0.92),
        context,
        tick=0,
        language="en",
    )

    assert monologue.agent_id == "alice"
    assert monologue.tick == 0
    assert "next steps" in monologue.text.lower()


def test_phase17_simulator_emits_exactly_one_monologue_per_agent_per_tick() -> None:
    simulator = Simulator(
        agents=[_agent("alice"), _agent("bob")],
        environment=_environment(),
        tick_duration_minutes=60,
    )

    simulator.run_ticks(2)

    assert len(simulator.logs) == 4
    assert len(simulator.monologues) == 4
    assert Counter(monologue.agent_id for monologue in simulator.monologues) == {"alice": 2, "bob": 2}
    assert Counter(monologue.tick for monologue in simulator.monologues) == {0: 2, 1: 2}


def test_phase17_monologue_text_is_not_shared_into_other_agents_decision_prompts() -> None:
    class RecordingLLM:
        def __init__(self) -> None:
            self.calls: list[list[dict[str, str]]] = []

        def complete(self, messages: object, **kwargs: object) -> str:
            snapshot = [
                {"role": str(message["role"]), "content": str(message["content"])}
                for message in messages
            ]
            self.calls.append(snapshot)
            user_content = snapshot[-1]["content"]
            if "private first-person thought" in user_content:
                agent_line = next(line for line in user_content.splitlines() if line.startswith("Agent: "))
                agent_name = agent_line.removeprefix("Agent: ")
                return f"I am {agent_name} and I keep this private."
            return '{"action_type": "observe", "target": null, "content": "stays quiet."}'

    llm = RecordingLLM()
    simulator = Simulator(
        agents=[_agent("alice"), _agent("bob")],
        environment=_environment(),
        tick_duration_minutes=60,
        llm=llm,
    )

    simulator.run_ticks(1)

    alice_monologue = next(
        monologue.text for monologue in simulator.monologues if monologue.agent_id == "alice"
    )
    bob_decision_call = next(
        call
        for call in llm.calls
        if "Persona ID: bob" in call[0]["content"] and 'Schema: {"action_type": str, "target": str | null, "content": str}' in call[1]["content"]
    )

    assert alice_monologue not in "\n".join(message["content"] for message in bob_decision_call)


def test_phase17_playground_exposes_inner_monologue_panel_and_result_markdown() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Test Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=1,
    )
    app = playground_app.build_app()
    components = _walk_components(app)

    monologue_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "inner-monologue-panel"
    )

    assert monologue_panel.label == playground_app.LABELS["ko"]["monologue_panel"]
    assert "t0" in result.monologue_markdown
