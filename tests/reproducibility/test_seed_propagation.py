from __future__ import annotations

from tests.reproducibility._helpers import (
    build_seeded_simulator,
    export_log_text,
    sha256_text,
)


def test_seed_is_propagated_to_personas_environment_and_actions() -> None:
    first = build_seeded_simulator(seed=20260418)
    second = build_seeded_simulator(seed=20260419)

    first_logs = first.run(duration_days=1)
    second_logs = second.run(duration_days=1)

    assert first.environment.conditions["seed"] == 20260418
    assert second.environment.conditions["seed"] == 20260419
    assert first.agents[0].goals[0] == "preserve seed 20260418"
    assert second.agents[0].goals[0] == "preserve seed 20260419"
    assert sha256_text(export_log_text(first_logs)) != sha256_text(export_log_text(second_logs))
