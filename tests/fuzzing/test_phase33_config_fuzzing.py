from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from knoema import load_config
from knoema.cli import load_run_config


@pytest.mark.parametrize(
    "payload",
    [
        "- not\n- a\n- mapping\n",
        "llm:\n  primary_provider: unknown\n",
        "memory:\n  short_term_capacity: 0\n",
        "runtime:\n  tick_duration_minutes: -1\n",
    ],
)
def test_phase33_core_config_fuzz_cases_reject_invalid_payloads(
    tmp_path: Path,
    payload: str,
) -> None:
    config_path = tmp_path / "knoema.yaml"
    config_path.write_text(payload, encoding="utf-8")

    with pytest.raises((ValueError, ValidationError)):
        load_config(config_path)


@pytest.mark.parametrize(
    "payload",
    [
        "agents: []\nenvironment:\n  start_time: 2026-04-18T09:00:00\n  location_path: [Lab]\n",
        "environment:\n  start_time: bad-date\n  location_path: [Lab]\nagents: []\n",
        "environment:\n  start_time: 2026-04-18T09:00:00\n  location_path: []\nagents: []\n",
        (
            "environment:\n"
            "  start_time: 2026-04-18T09:00:00\n"
            "  location_path: [Lab]\n"
            "agents:\n"
            "  - agent_id: alice\n"
            "    name: Alice\n"
            "    age: 19\n"
            "    background: Synthetic participant\n"
            "    personality:\n"
            "      openness: 2\n"
            "      conscientiousness: 0.5\n"
            "      extraversion: 0.5\n"
            "      agreeableness: 0.5\n"
            "      neuroticism: 0.5\n"
        ),
    ],
)
def test_phase33_cli_config_fuzz_cases_reject_invalid_payloads(
    tmp_path: Path,
    payload: str,
) -> None:
    config_path = tmp_path / "run.yaml"
    config_path.write_text(payload, encoding="utf-8")

    with pytest.raises((ValueError, ValidationError)):
        load_run_config(config_path)
