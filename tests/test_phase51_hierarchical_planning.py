from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from luvoire import (
    AgentContext,
    Environment,
    HierarchicalPlanner,
    LocalClient,
    Persona,
    Personality,
    Simulator,
    WorldState,
)
from luvoire.decision import build_decision_messages
from luvoire.types import Emotion


def _persona(*, planning: bool = False) -> Persona:
    return Persona(
        agent_id="researcher",
        name="Researcher",
        age=31,
        background="Synthetic researcher preparing an experiment.",
        personality=Personality(0.7, 0.8, 0.4, 0.6, 0.3),
        goals=["complete a paper experiment"],
        planning=planning,
    )


def test_phase51_persona_keeps_planning_opt_in() -> None:
    default_persona = _persona()
    planning_persona = _persona(planning=True)

    assert default_persona.planning is False
    assert planning_persona.planning is True
    assert "Hierarchical planning: enabled" in planning_persona.to_system_prompt()


def test_phase51_planner_decomposes_selects_and_updates_tasks() -> None:
    planner = HierarchicalPlanner(default_depth=3)
    tasks = planner.decompose(
        "complete a paper experiment",
        AgentContext(
            agent_id="researcher",
            location="Lab",
            active_goals=("complete a paper experiment",),
        ),
    )

    assert len(tasks) == 3
    assert tasks[0].children == [tasks[1].task_id]
    assert tasks[1].parent_id == tasks[0].task_id

    selected = planner.select_next_task("researcher", WorldState(tick=0))
    assert selected is not None
    assert selected.description.startswith("Clarify")
    planner.update_progress("researcher", selected)

    second = planner.select_next_task("researcher", WorldState(tick=1))
    assert second is not None
    assert second.parent_id == selected.task_id


def test_phase51_replan_on_failure_adds_recovery_task() -> None:
    planner = HierarchicalPlanner(default_depth=2)
    tasks = planner.decompose(
        "finish field notes",
        AgentContext(agent_id="researcher", location="Lab", plan_depth=2),
    )
    recovery_plan = planner.replan_on_failure("researcher", tasks[0])

    assert recovery_plan[-1].task_id.endswith(":replan")
    assert recovery_plan[-1].priority >= tasks[0].priority


def test_phase51_decision_prompt_includes_current_task() -> None:
    planner = HierarchicalPlanner(default_depth=2)
    planner.decompose(
        "complete a paper experiment",
        AgentContext(agent_id="researcher", location="Lab", plan_depth=2),
    )
    current_task = planner.select_next_task("researcher", WorldState())
    assert current_task is not None

    environment = Environment(
        start_time=datetime(2026, 4, 19, 9, 0),
        location_path=("Lab",),
    )
    messages = build_decision_messages(
        persona=_persona(planning=True),
        memories=[],
        relationships={},
        environment=environment.get_context("researcher"),
        emotion=Emotion(0.0, 0.2, 0.5),
        trigger=None,
        current_task=current_task,
    )

    assert "Current hierarchical task" in messages[1]["content"]
    assert "complete a paper experiment" in messages[1]["content"]


def test_phase51_simulator_advances_planning_tasks() -> None:
    simulator = Simulator(
        agents=[_persona(planning=True)],
        environment=Environment(
            start_time=datetime(2026, 4, 19, 9, 0),
            location_path=("Lab",),
        ),
        llm=LocalClient(
            lambda _: '{"action_type": "work", "target": null, "content": "advances the planned task."}'
        ),
    )

    simulator.run_ticks(3)

    assert simulator.planner.achievement_rate(["researcher"]) == 1.0


def test_phase51_experiment_summary_meets_acceptance_gate() -> None:
    subprocess.run(
        [sys.executable, "experiments/planning_depth/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/planning_depth/results/summary.json").read_text(encoding="utf-8")
    )

    assert summary["acceptance"]["three_level_goal_achievement_at_least_0_85"] is True
    assert summary["results"]["3"]["goal_achievement_rate"] >= 0.85
    assert summary["results"]["3"]["planning_off_goal_achievement_rate"] <= 0.65


def test_phase51_docs_and_notebook_are_linked() -> None:
    assert Path("docs/cognition/hierarchical_planning.md").exists()
    assert Path("examples/08_hierarchical_goal_pursuit.ipynb").exists()
    assert "Hierarchical Planning: cognition/hierarchical_planning.md" in Path(
        "mkdocs.yml"
    ).read_text(encoding="utf-8")
    assert "planning-depth experiment" in Path("paper/sections/03_architecture.tex").read_text(
        encoding="utf-8"
    )
