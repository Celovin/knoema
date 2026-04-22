"""Phase 43 tests for persona opt-in theory of mind."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from luvoire import (
    EnvironmentContext,
    Memory,
    Persona,
    Personality,
    Relationship,
    TheoryOfMindEngine,
    TheoryOfMindProfile,
    render_persona_system_prompt,
)
from luvoire.decision import build_decision_messages
from luvoire.theory_of_mind import run_sally_anne_benchmark
from luvoire.types import Emotion


def _reasoner() -> Persona:
    return Persona(
        agent_id="anne",
        name="Anne",
        age=9,
        background="Observes where others last saw shared objects.",
        personality=Personality(0.6, 0.7, 0.5, 0.7, 0.2),
        values=["clarity"],
        goals=["track what others know"],
        theory_of_mind=TheoryOfMindProfile(enabled=True),
    )


def _subject() -> Persona:
    return Persona(
        agent_id="sally",
        name="Sally",
        age=9,
        background="Looks for objects where she last saw them.",
        personality=Personality(0.5, 0.6, 0.5, 0.6, 0.2),
        values=["consistency"],
        goals=["find the object"],
    )


def _mover() -> Persona:
    return Persona(
        agent_id="bob",
        name="Bob",
        age=9,
        background="Moves an object after Sally leaves.",
        personality=Personality(0.4, 0.5, 0.6, 0.5, 0.3),
        values=["curiosity"],
        goals=["move the object"],
    )


def test_phase43_persona_keeps_theory_of_mind_opt_in() -> None:
    default_persona = _subject()
    reasoner = _reasoner()

    assert default_persona.theory_of_mind.enabled is False
    assert reasoner.theory_of_mind.enabled is True
    assert "Theory of mind: enabled" in reasoner.to_system_prompt()
    assert "Theory of mind: enabled" in render_persona_system_prompt(reasoner)


def test_phase43_engine_tracks_false_beliefs_for_opt_in_personas() -> None:
    engine = TheoryOfMindEngine.from_personas([_reasoner(), _subject(), _mover()])
    engine.seed_shared_belief("marble", "basket")
    engine.move_object("marble", "box", actor_id="bob", witnesses=["anne", "bob"])

    context = engine.context_for("anne")

    assert context is not None
    assert engine.belief_for("sally", "marble") == "basket"
    assert engine.modeled_belief("anne", "sally", "marble") == "basket"
    assert any("sally thinks the marble is in basket" in line for line in context.render_lines())


def test_phase43_decision_messages_include_theory_of_mind_section() -> None:
    engine = TheoryOfMindEngine.from_personas([_reasoner(), _subject(), _mover()])
    engine.seed_shared_belief("marble", "basket")
    engine.move_object("marble", "box", actor_id="bob", witnesses=["anne", "bob"])
    context = engine.context_for("anne")
    assert context is not None

    messages = build_decision_messages(
        persona=_reasoner(),
        memories=[
            Memory(
                id="mem-anne-1",
                agent_id="anne",
                timestamp=datetime(2026, 4, 19, 11, 55),
                content="Sally last saw the marble in the basket.",
                memory_type="episodic",
                importance=0.8,
            )
        ],
        relationships={"sally": Relationship(source="anne", target="sally", weight=0.6, trust=0.7)},
        environment=EnvironmentContext(
            agent_id="anne",
            timestamp=datetime(2026, 4, 19, 12, 0),
            location_path=("Playroom",),
            conditions={"task": "predict search location"},
        ),
        emotion=Emotion(valence=0.1, arousal=0.3, dominance=0.6),
        trigger=None,
        theory_of_mind_context=context,
        language="en",
    )

    assert "Theory of mind:" in messages[1]["content"]
    assert "sally thinks the marble is in basket" in messages[1]["content"]


def test_phase43_sally_anne_benchmark_meets_target() -> None:
    result = run_sally_anne_benchmark()

    assert result.passed is True
    assert result.accuracy >= 0.8
    assert result.correct_cases == result.total_cases == 20


def test_phase43_docs_reports_and_paper_reflect_theory_of_mind() -> None:
    matrix = Path("docs/competitor_matrix.md").read_text(encoding="utf-8")
    summary = Path("benchmarks/formal_report/results/summary.md").read_text(encoding="utf-8")
    paper_body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            Path("paper/abstract.tex"),
            Path("paper/sections/02_related_work.tex"),
            Path("paper/sections/03_architecture.tex"),
            Path("paper/sections/04_experiments.tex"),
            Path("paper/tables/theory_of_mind_summary.tex"),
        ]
    )

    assert "Theory of mind surface" in matrix
    assert "Sally-Anne" in matrix
    assert "persona opt-in" in matrix
    assert "Sally-Anne reproduction" in summary
    assert "Theory-of-mind source" in summary
    assert "persona opt-in theory-of-mind" in paper_body
    assert "Sally-Anne" in paper_body
    assert "20/20 (1.000)" in paper_body
