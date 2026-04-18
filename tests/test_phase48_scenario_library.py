"""Phase 48 tests for the 50-scenario marketplace library."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema.dsl import collect_validation_issues, load_scenario

LIBRARY_ROOT = Path("scenarios/library")
EXPECTED_CATEGORIES = [
    "community",
    "family",
    "school",
    "social_experiment",
    "workplace",
]


def test_phase48_library_files_cover_five_categories_with_fifty_scenarios() -> None:
    categories = sorted(path.name for path in LIBRARY_ROOT.iterdir() if path.is_dir())
    yaml_files = sorted(LIBRARY_ROOT.glob("*/*.yaml"))
    md_files = sorted(LIBRARY_ROOT.glob("*/*.md"))

    assert categories == EXPECTED_CATEGORIES
    assert len(yaml_files) == 50
    assert len(md_files) == 50
    assert (LIBRARY_ROOT / "INDEX.md").exists()

    for category in EXPECTED_CATEGORIES:
        assert len(list((LIBRARY_ROOT / category).glob("*.yaml"))) == 10
        assert len(list((LIBRARY_ROOT / category).glob("*.md"))) == 10


def test_phase48_all_scenarios_load_validate_and_smoke_run_five_ticks() -> None:
    for path in sorted(LIBRARY_ROOT.glob("*/*.yaml")):
        scenario = load_scenario(path)
        md_path = path.with_suffix(".md")
        simulator = scenario.to_simulator()
        logs = simulator.run_ticks(5)

        assert scenario.scenario_id == path.stem
        assert collect_validation_issues(scenario) == []
        assert len(logs) == len(scenario.agents) * 5
        assert md_path.exists()
        assert "fictional" in md_path.read_text(encoding="utf-8").casefold()


def test_phase48_social_experiment_scenarios_are_ethics_gated() -> None:
    for path in sorted((LIBRARY_ROOT / "social_experiment").glob("*.yaml")):
        scenario = load_scenario(path)
        scenario_doc = path.with_suffix(".md").read_text(encoding="utf-8")

        assert scenario.ethics.fictional is True
        assert scenario.ethics.no_real_people is True
        assert scenario.ethics.no_prediction is True
        assert scenario.ethics.no_suspect_scoring is True
        assert scenario.ethics.sensitive_domain is True
        assert scenario.ethics.irb_notes
        assert "Ethics guardrail complete" in scenario_doc


def test_phase48_cli_validate_accepts_library_directory() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knoema.cli",
            "validate",
            str(LIBRARY_ROOT),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["validated"] == 50
    assert payload["failed"] == 0
    assert all(row["ok"] for row in payload["results"])


def test_phase48_index_lists_every_scenario() -> None:
    index = (LIBRARY_ROOT / "INDEX.md").read_text(encoding="utf-8")

    for path in sorted(LIBRARY_ROOT.glob("*/*.yaml")):
        assert str(path.relative_to(LIBRARY_ROOT)).replace("\\", "/") in index
