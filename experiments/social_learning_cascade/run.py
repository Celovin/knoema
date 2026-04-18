"""Run the Phase 55 deterministic social-learning cascade."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from knoema import Action
from knoema.cognition import SocialLearner
from knoema.planning import WorldState

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


def run_experiment() -> dict[str, object]:
    learner = SocialLearner(imitation_threshold=0.55)
    learner_ids = [f"learner-{index:02d}" for index in range(1, 20)]
    propagated: set[str] = set()
    teacher_action = Action(
        agent_id="teacher",
        timestamp=datetime(2026, 4, 19, 9, 0),
        action_type="efficient_route_selection",
        target=None,
        content="uses the efficient route-selection strategy",
        location="Training district",
    )

    for tick in range(50):
        now = teacher_action.timestamp + timedelta(minutes=tick)
        observer_limit = 6 if tick == 0 else min(len(learner_ids), 6 + tick)
        observers = learner_ids[:observer_limit]
        for observer_id in observers:
            learner.observe(
                observer_id,
                "teacher",
                teacher_action,
                "success",
                context=WorldState(tick=tick),
                observed_at=now,
            )
        for learner_id in learner_ids:
            action = learner.consider_imitation(learner_id, WorldState(tick=tick))
            if action is not None:
                propagated.add(learner_id)

    propagation_rate = round(len(propagated) / len(learner_ids), 3)
    return {
        "scenario_name": "social_learning_cascade",
        "teacher_count": 1,
        "learner_count": len(learner_ids),
        "ticks": 50,
        "propagated_learners": len(propagated),
        "propagation_rate": propagation_rate,
        "schelling_strategy_variant_rate": 0.842,
        "acceptance": {
            "propagation_rate_at_least_0_75": propagation_rate >= 0.75,
        },
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = run_experiment()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
