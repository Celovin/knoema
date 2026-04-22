from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from luvoire.dsl import collect_validation_issues, load_scenario


def test_phase37_hub_files_exist() -> None:
    expected = [
        Path(".github/PULL_REQUEST_TEMPLATE/scenario_submission.md"),
        Path(".github/workflows/scenario-hub.yml"),
        Path("scripts/validate_scenarios.py"),
        Path("scenarios_hub/README.md"),
        Path("scenarios_hub/submissions/_template.yaml"),
    ]

    for path in expected:
        assert path.exists(), path


def test_phase37_curated_scenarios_cover_four_categories_with_ten_seed_files() -> None:
    curated_root = Path("scenarios_hub/curated")
    categories = sorted(path.name for path in curated_root.iterdir() if path.is_dir())
    curated_files = sorted(curated_root.rglob("*.yaml"))

    assert categories == ["education", "game_demo", "research", "social"]
    assert len(curated_files) == 10


def test_phase37_curated_scenarios_parse_validate_and_match_filenames() -> None:
    for path in sorted(Path("scenarios_hub/curated").rglob("*.yaml")):
        scenario = load_scenario(path)
        simulator = scenario.to_simulator()
        logs = simulator.run(duration_days=scenario.duration_days)

        assert scenario.scenario_id == path.stem
        assert collect_validation_issues(scenario) == []
        assert len(logs) >= len(scenario.agents)


def test_phase37_submission_template_and_readme_surface_review_flow() -> None:
    template = yaml.safe_load(
        Path("scenarios_hub/submissions/_template.yaml").read_text(encoding="utf-8")
    )
    readme = Path("scenarios_hub/README.md").read_text(encoding="utf-8")
    pr_template = Path(".github/PULL_REQUEST_TEMPLATE/scenario_submission.md").read_text(
        encoding="utf-8"
    )

    assert template["schema_version"] == "1.0"
    assert "ethics" in template
    assert "GitHub Discussion" in readme
    assert "validate_scenarios.py" in readme
    assert "scenario_submission.md" in readme
    assert "I ran `python scripts/validate_scenarios.py`" in pr_template
    assert "No real people" in pr_template


def test_phase37_validator_workflow_and_script_execute_successfully() -> None:
    workflow = Path(".github/workflows/scenario-hub.yml").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/validate_scenarios.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert 'name: Scenario Hub' in workflow
    assert 'python scripts/validate_scenarios.py' in workflow
    assert 'scenarios_hub/**' in workflow
    assert result.returncode == 0, result.stderr or result.stdout
    assert '"validated": 10' in result.stdout
