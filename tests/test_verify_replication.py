from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")
verify_replication = importlib.import_module("scripts.verify_replication")


def _sample_replication_archive() -> Path:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Verifier Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
    )
    return Path(
        playground_app._export_replication_package(
            result.jsonl,
            result.memory_snapshot,
            "Mode: Replay only | Agents: 2",
            "English",
        )
    )


def test_verify_replication_inspects_archive_members() -> None:
    archive_path = _sample_replication_archive()

    try:
        report = verify_replication.inspect_replication_archive(archive_path)

        assert report["missing_members"] == []
        assert report["jsonl_row_count"] > 0
        assert "source_files" in report["manifest_keys"]
    finally:
        archive_path.unlink(missing_ok=True)


def test_verify_replication_runs_pytest_probe() -> None:
    archive_path = _sample_replication_archive()

    try:
        report = verify_replication.verify_replication_package(archive_path, run_pytest=True)

        assert report["verification_passed"] is True
        assert report["pytest_exit_code"] == 0
        assert "1 passed" in report["pytest_stdout"]
    finally:
        archive_path.unlink(missing_ok=True)
