"""Determinism + invariants test for the RAT sensitivity experiment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.rat_sensitivity import run as experiment

RESULTS_DIR = Path(experiment.__file__).parent / "results"
COMMITTED_INDICES_PATH = RESULTS_DIR / "sobol_indices.json"
COMMITTED_MANIFEST_PATH = RESULTS_DIR / "run_manifest.json"


def test_run_is_deterministic_per_seed() -> None:
    indices_a = experiment.run(seed=20260427, n=512)
    indices_b = experiment.run(seed=20260427, n=512)
    for name in indices_a.variable_names:
        a_entry = indices_a.as_dict()[name]
        b_entry = indices_b.as_dict()[name]
        assert a_entry["first_order"] == pytest.approx(b_entry["first_order"])
        assert a_entry["total_order"] == pytest.approx(b_entry["total_order"])


def test_run_changes_with_seed() -> None:
    indices_a = experiment.run(seed=1, n=512)
    indices_b = experiment.run(seed=2, n=512)
    a_first = indices_a.first_order
    b_first = indices_b.first_order
    assert not (
        a_first[0] == pytest.approx(b_first[0])
        and a_first[1] == pytest.approx(b_first[1])
        and a_first[2] == pytest.approx(b_first[2])
    )


def test_committed_indices_match_default_run() -> None:
    payload = json.loads(COMMITTED_INDICES_PATH.read_text(encoding="utf-8"))
    indices = experiment.run(
        seed=payload["seed"],
        n=payload["n"],
    )
    for name in indices.variable_names:
        committed = payload["variables"][name]
        recomputed = indices.as_dict()[name]
        assert recomputed["first_order"] == pytest.approx(
            committed["first_order"]
        )
        assert recomputed["total_order"] == pytest.approx(
            committed["total_order"]
        )


def test_three_variables_are_close_to_symmetric_under_multiplicative_model() -> None:
    payload = json.loads(COMMITTED_INDICES_PATH.read_text(encoding="utf-8"))
    first_orders = [
        payload["variables"][name]["first_order"]
        for name in ("motivation", "exposure", "gap")
    ]
    total_orders = [
        payload["variables"][name]["total_order"]
        for name in ("motivation", "exposure", "gap")
    ]
    spread_first = max(first_orders) - min(first_orders)
    spread_total = max(total_orders) - min(total_orders)
    assert spread_first < 0.05, "multiplicative RAT model should produce symmetric first-order"
    assert spread_total < 0.05, "multiplicative RAT model should produce symmetric total-order"


def test_total_order_exceeds_first_order_due_to_interaction() -> None:
    payload = json.loads(COMMITTED_INDICES_PATH.read_text(encoding="utf-8"))
    for name, entry in payload["variables"].items():
        assert entry["total_order"] > entry["first_order"], (
            f"variable {name}: multiplicative model implies S_T > S_1 "
            f"due to interactions"
        )


def test_run_manifest_records_module_version_and_estimator() -> None:
    manifest = json.loads(COMMITTED_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["experiment"] == "rat_sensitivity"
    assert manifest["module_version"] == "luvoire.theory.rat.v1"
    assert "saltelli" in manifest["estimator"].lower()
    assert manifest["variables"] == ["motivation", "exposure", "gap"]
