from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from knoema.cli import main, run_config


def _write_run_config(path: Path, output_name: str = "cli_logs.jsonl") -> None:
    path.write_text(
        "\n".join(
            [
                "runtime:",
                "  duration_days: 1",
                "  tick_duration_minutes: 720",
                f"  output_path: {output_name}",
                "  prompt_language: ko",
                "environment:",
                '  start_time: "2026-03-02T09:00:00"',
                "  location_path: [Korea, Seoul, Dormitory]",
                "  conditions:",
                "    weather: clear",
                "agents:",
                "  - agent_id: alice",
                "    name: Alice",
                "    age: 17",
                "    background: Dormitory student.",
                "    personality:",
                "      openness: 0.8",
                "      conscientiousness: 0.6",
                "      extraversion: 0.2",
                "      agreeableness: 0.7",
                "      neuroticism: 0.4",
                "    values: [privacy]",
                "    goals: [finish a short story]",
                "  - agent_id: bob",
                "    name: Bob",
                "    age: 17",
                "    background: Science student.",
                "    personality:",
                "      openness: 0.6",
                "      conscientiousness: 0.8",
                "      extraversion: 0.9",
                "      agreeableness: 0.7",
                "      neuroticism: 0.3",
                "    values: [teamwork]",
                "    goals: [prepare for a contest]",
                "events:",
                "  - timestamp: \"2026-03-02T09:00:00\"",
                "    event_type: dorm.announcement",
                "    participants: [alice, bob]",
                "    location: Korea > Seoul > Dormitory",
                "    description: Morning study period begins.",
                "local_response: '{\"action_type\": \"observe\", \"target\": null, \"content\": \"records the routine.\"}'",
            ]
        ),
        encoding="utf-8",
    )


def test_phase14_cli_run_config_writes_jsonl_relative_to_config(tmp_path: Path) -> None:
    config_path = tmp_path / "run.yaml"
    _write_run_config(config_path)

    summary = run_config(config_path)

    output_path = tmp_path / "cli_logs.jsonl"
    lines = output_path.read_text(encoding="utf-8").splitlines()
    first_row = json.loads(lines[0])

    assert summary.log_count == 4
    assert summary.prompt_language == "ko"
    assert len(lines) == 4
    assert first_row["action"]["action_type"] == "observe"


def test_phase14_cli_main_supports_output_override_and_json_summary(
    tmp_path: Path,
    capsys,  # type: ignore[no-untyped-def]
) -> None:
    config_path = tmp_path / "run.yaml"
    output_path = tmp_path / "override.jsonl"
    _write_run_config(config_path)

    exit_code = main(["run", str(config_path), "--output", str(output_path), "--json"])

    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["output_path"] == str(output_path)
    assert summary["log_count"] == 4
    assert output_path.exists()


def test_phase14_cli_dry_run_does_not_write_output(tmp_path: Path) -> None:
    config_path = tmp_path / "run.yaml"
    _write_run_config(config_path)

    summary = run_config(config_path, dry_run=True)

    assert summary.log_count == 0
    assert not (tmp_path / "cli_logs.jsonl").exists()


def test_phase14_cli_module_and_entry_point_are_available(tmp_path: Path) -> None:
    config_path = tmp_path / "run.yaml"
    output_path = tmp_path / "module.jsonl"
    _write_run_config(config_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knoema.cli",
            "run",
            str(config_path),
            "--output",
            str(output_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert json.loads(result.stdout)["log_count"] == 4
    assert pyproject["project"]["scripts"]["knoema"] == "knoema.cli:main"
