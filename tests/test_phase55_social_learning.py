from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from luvoire import (
    Action,
    Environment,
    LocalClient,
    Persona,
    Personality,
    Simulator,
    SocialLearner,
)
from luvoire.planning import WorldState


def _persona(agent_id: str, *, social_learning: bool = False) -> Persona:
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=28,
        background="Synthetic social-learning participant.",
        personality=Personality(0.6, 0.7, 0.5, 0.8, 0.2),
        goals=["learn a useful routine"],
        social_learning=social_learning,
    )


def test_phase55_persona_keeps_social_learning_opt_in() -> None:
    default = _persona("default")
    learner = _persona("learner", social_learning=True)

    assert default.social_learning is False
    assert learner.social_learning is True
    assert "Social learning: enabled" in learner.to_system_prompt()


def test_phase55_social_learner_observes_retains_and_imitates_successful_action() -> None:
    learner = SocialLearner()
    action = Action(
        agent_id="teacher",
        timestamp=datetime(2026, 4, 19, 9, 0),
        action_type="efficient_route_selection",
        target=None,
        content="uses an efficient strategy",
        location="Training district",
    )

    learner.observe("student", "teacher", action, "success", context=WorldState(tick=1))
    imitation = learner.consider_imitation("student", WorldState(tick=2))

    assert imitation is not None
    assert imitation.agent_id == "student"
    assert imitation.action_type == "efficient_route_selection"
    assert "Imitates teacher" in imitation.content
    assert learner.get_skill_library("student")[0].motivation_score >= 0.55


def test_phase55_simulator_lets_opt_in_agent_imitate_prior_agent_action() -> None:
    simulator = Simulator(
        agents=[_persona("teacher"), _persona("student", social_learning=True)],
        environment=Environment(
            start_time=datetime(2026, 4, 19, 9, 0),
            location_path=("Training district",),
        ),
        llm=LocalClient(
            lambda _: (
                '{"action_type": "efficient_route_selection", '
                '"target": null, "content": "uses an efficient strategy"}'
            )
        ),
    )

    logs = simulator.run_ticks(1)

    assert logs[0].agent_id == "teacher"
    assert logs[1].agent_id == "student"
    assert logs[1].action.action_type == "efficient_route_selection"
    assert "Imitates teacher" in logs[1].action.content


def test_phase55_experiment_summary_meets_propagation_gate() -> None:
    subprocess.run(
        [sys.executable, "experiments/social_learning_cascade/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/social_learning_cascade/results/summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["acceptance"]["propagation_rate_at_least_0_75"] is True
    assert summary["propagation_rate"] >= 0.75


def test_phase55_docs_and_paper_reference_social_learning() -> None:
    assert "Social Learning: cognition/social_learning.md" in Path("mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "Social Learning Cascade" in Path("paper/sections/04_experiments.tex").read_text(
        encoding="utf-8"
    )
    assert Path("docs/cognition/social_learning.md").exists()
