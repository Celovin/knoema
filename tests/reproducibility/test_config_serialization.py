from __future__ import annotations

from pathlib import Path

import yaml

from luvoire.cli import load_run_config


def test_yaml_run_config_round_trips_through_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "scenario.yaml"
    config_path.write_text(
        "\n".join(
            [
                "runtime:",
                "  duration_days: 1",
                "  tick_duration_minutes: 720",
                "  output_path: replay.jsonl",
                "  prompt_language: en",
                "environment:",
                "  start_time: 2026-06-01T09:00:00",
                "  location_path: [Luvoire Demo World, Reproducibility Lab]",
                "  conditions:",
                "    seed: 20260418",
                "agents:",
                "  - agent_id: alice",
                "    name: Alice",
                "    age: 24",
                "    background: Synthetic participant.",
                "    personality:",
                "      openness: 0.5",
                "      conscientiousness: 0.6",
                "      extraversion: 0.4",
                "      agreeableness: 0.7",
                "      neuroticism: 0.2",
                "    values: [repeatability]",
                "    goals: [round trip config]",
            ]
        ),
        encoding="utf-8",
    )

    first = load_run_config(config_path)
    round_trip_path = tmp_path / "scenario_round_trip.yaml"
    round_trip_path.write_text(
        yaml.safe_dump(first.model_dump(mode="json"), sort_keys=True),
        encoding="utf-8",
    )
    second = load_run_config(round_trip_path)

    assert second.model_dump(mode="json") == first.model_dump(mode="json")
