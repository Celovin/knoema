"""Smoke tests for ASC 2026 abstract artifacts and zenodo metadata bump."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTER_DIR = ROOT / "paper" / "asc2026_poster"
ZENODO = ROOT / ".zenodo.json"


def test_abstract_en_exists_and_mentions_rat() -> None:
    text = (POSTER_DIR / "abstract_en.md").read_text(encoding="utf-8")
    assert "Routine Activity Theory" in text
    assert "ASC 2026" in text
    assert "no_real_geometry" in text
    assert "Sobol" in text


def test_abstract_ko_exists_and_mentions_rat() -> None:
    text = (POSTER_DIR / "abstract_ko.md").read_text(encoding="utf-8")
    assert "일상활동이론" in text
    assert "Sobol" in text
    assert "no_real_geometry" in text


def test_ethics_footer_canonical_text_present() -> None:
    text = (POSTER_DIR / "ethics_footer.md").read_text(encoding="utf-8")
    assert "fictional, synthetic, non-identifying" in text
    assert "POLICIES/civilian_use.md" in text
    assert "verify_replay_shas.py" in text


def test_zenodo_keywords_include_routine_activity_theory() -> None:
    payload = json.loads(ZENODO.read_text(encoding="utf-8"))
    assert "routine activity theory" in payload["keywords"]
    assert "auditable replay" in payload["keywords"]
    assert "sensitivity analysis" in payload["keywords"]


def test_zenodo_notes_describe_unreleased_additions() -> None:
    payload = json.loads(ZENODO.read_text(encoding="utf-8"))
    notes = payload["notes"]
    assert "Scenario DSL v2" in notes
    assert "luvoire.theory.rat.v1" in notes
    assert "Saltelli" in notes
    assert "ASC 2026" in notes
