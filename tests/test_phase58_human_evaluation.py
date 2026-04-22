from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import yaml

from luvoire.evaluation import (
    ComparisonPair,
    EvaluationSession,
    cohen_kappa,
    compute_inter_rater_reliability,
    fleiss_kappa,
)

NPM = "npm.cmd" if os.name == "nt" else "npm"


def test_phase58_human_evaluation_files_exist() -> None:
    expected = [
        "src/luvoire/evaluation/__init__.py",
        "src/luvoire/evaluation/human.py",
        "evaluation/templates/realism_survey.yaml",
        "evaluation/templates/preference_pairwise.yaml",
        "evaluation/templates/turing_style.yaml",
        "evaluation/samples/pilot_ratings.json",
        "evaluation/web/package.json",
        "evaluation/web/public/index.html",
        "docs/evaluation/human_study_protocol.md",
        "docs/evaluation/pilot_results.md",
    ]

    for path in expected:
        assert Path(path).exists()


def test_phase58_reliability_metrics_compute_for_sample_pilot() -> None:
    payload = json.loads(Path("evaluation/samples/pilot_ratings.json").read_text(encoding="utf-8"))
    report = compute_inter_rater_reliability(payload["ratings_by_item"])

    assert report.item_count == 6
    assert report.rater_count == 5
    assert report.categories == ("left", "right", "tie")
    assert report.pairwise_cohen_kappa >= 0.6
    assert report.fleiss_kappa >= 0.6
    assert report.passes_pilot_gate is True


def test_phase58_cohen_and_fleiss_known_cases() -> None:
    assert cohen_kappa(["left", "right", "tie"], ["left", "right", "tie"]) == 1.0
    assert fleiss_kappa(
        [
            {"left": 3, "right": 0},
            {"left": 0, "right": 3},
            {"left": 3, "right": 0},
        ]
    ) == 1.0


def test_phase58_evaluation_session_tracks_completed_ratings() -> None:
    session = EvaluationSession(
        session_id="pilot",
        title="Pilot",
        comparison_pairs=[
            ComparisonPair(
                pair_id="pair_001",
                left_trace_id="trace_a",
                right_trace_id="trace_b",
                prompt="Which trace preserves memory better?",
            )
        ],
        rater_ids=["rater_a", "rater_b"],
    )

    session.add_rating("pair_001", "rater_a", "left")
    session.add_rating("pair_001", "rater_b", "left")

    assert session.completed_rating_matrix() == {
        "pair_001": {"rater_a": "left", "rater_b": "left"}
    }
    assert session.reliability().fleiss_kappa == 1.0
    assert session.to_payload()["completed_pair_count"] == 1


def test_phase58_templates_have_required_shapes() -> None:
    realism = yaml.safe_load(Path("evaluation/templates/realism_survey.yaml").read_text())
    preference = yaml.safe_load(Path("evaluation/templates/preference_pairwise.yaml").read_text())
    turing = yaml.safe_load(Path("evaluation/templates/turing_style.yaml").read_text())

    assert len(realism["items"]) == 15
    assert preference["labels"] == ["left", "right", "tie"]
    assert "unsure" in turing["labels"]


def test_phase58_web_scaffold_scripts_and_docs_are_linked() -> None:
    package = json.loads(Path("evaluation/web/package.json").read_text(encoding="utf-8"))
    assert {"dev", "build", "test"} <= set(package["scripts"])

    subprocess.run([NPM, "--prefix", "evaluation/web", "run", "test"], check=True, cwd=Path.cwd())

    docs = Path("docs/evaluation/human_study_protocol.md").read_text(encoding="utf-8")
    checklist_count = sum(1 for line in docs.splitlines() if line.startswith("- [ ]"))
    assert checklist_count >= 20
    assert "Human Study Protocol: evaluation/human_study_protocol.md" in Path(
        "mkdocs.yml"
    ).read_text(encoding="utf-8")
