"""Tests for scripts.run_id."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_id import (
    code_tree_sha,
    compute_run_id,
    env_sha,
    scenario_yaml_sha,
)

ROOT = Path(__file__).resolve().parents[1]
V2_BASELINE = ROOT / "tests" / "fixtures" / "scenarios" / "v2_rat_baseline.yaml"


def test_code_tree_sha_is_deterministic() -> None:
    a = code_tree_sha()
    b = code_tree_sha()
    assert a == b
    assert len(a) == 64


def test_scenario_yaml_sha_is_deterministic() -> None:
    a = scenario_yaml_sha(V2_BASELINE)
    b = scenario_yaml_sha(V2_BASELINE)
    assert a == b
    assert len(a) == 64


def test_env_sha_canonicalises_input_order() -> None:
    a = env_sha(["numpy==2.4.4", "pydantic==2.8"])
    b = env_sha(["pydantic==2.8", "numpy==2.4.4"])
    assert a == b


def test_env_sha_ignores_blank_lines() -> None:
    a = env_sha(["numpy==2.4.4", "", "pydantic==2.8"])
    b = env_sha(["numpy==2.4.4", "pydantic==2.8"])
    assert a == b


def test_compute_run_id_returns_full_payload() -> None:
    payload = compute_run_id(scenario_yaml=V2_BASELINE, seed=1)
    assert "run_id" in payload
    assert "code_tree_sha" in payload
    assert "scenario_yaml_sha" in payload
    assert payload["seed"] == 1
    assert "python_version" in payload


def test_compute_run_id_changes_with_seed() -> None:
    a = compute_run_id(scenario_yaml=V2_BASELINE, seed=1)
    b = compute_run_id(scenario_yaml=V2_BASELINE, seed=2)
    assert a["run_id"] != b["run_id"]
    assert a["code_tree_sha"] == b["code_tree_sha"]


def test_compute_run_id_changes_with_env() -> None:
    a = compute_run_id(
        scenario_yaml=V2_BASELINE, seed=1, pip_freeze_lines=["numpy==2.4.4"]
    )
    b = compute_run_id(
        scenario_yaml=V2_BASELINE, seed=1, pip_freeze_lines=["numpy==2.4.5"]
    )
    assert a["run_id"] != b["run_id"]


def test_code_tree_sha_missing_dir_raises() -> None:
    with pytest.raises(FileNotFoundError):
        code_tree_sha(Path("does_not_exist"))
