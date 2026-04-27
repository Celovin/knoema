"""Smoke tests for the RAT methodology paper drafts (T4.5)."""

from __future__ import annotations

from pathlib import Path

DRAFT_DIR = Path(__file__).resolve().parents[1] / "paper" / "rat_methodology"


def test_kci_draft_present_and_korean() -> None:
    text = (DRAFT_DIR / "kci_draft.md").read_text(encoding="utf-8")
    assert "일상활동이론" in text
    assert "Civilian Use" in text
    assert "no_real_geometry" in text
    assert "POLICIES/civilian_use.md" in text


def test_ssci_draft_present_and_english() -> None:
    text = (DRAFT_DIR / "ssci_draft.md").read_text(encoding="utf-8")
    assert "Routine Activity Theory" in text or "routine activity theory" in text
    assert "no_real_geometry" in text
    assert "Civilian-use statement" in text
    assert "Saltelli" in text


def test_methodology_section_shared_canonical_text() -> None:
    text = (DRAFT_DIR / "methodology_section.md").read_text(encoding="utf-8")
    assert "Tier A" in text
    assert "Tier B" in text
    assert "Tier C" in text
    assert "Sobol" in text
    assert "POLICIES/civilian_use.md" in text


def test_readme_present() -> None:
    text = (DRAFT_DIR / "README.md").read_text(encoding="utf-8")
    assert "kci_draft.md" in text
    assert "ssci_draft.md" in text
    assert "methodology_section.md" in text


def test_drafts_cite_crimemind() -> None:
    for name in ("kci_draft.md", "ssci_draft.md"):
        text = (DRAFT_DIR / name).read_text(encoding="utf-8")
        assert "CrimeMind" in text
        assert "2506.05981" in text


def test_drafts_disclaim_prediction() -> None:
    text_kci = (DRAFT_DIR / "kci_draft.md").read_text(encoding="utf-8")
    text_ssci = (DRAFT_DIR / "ssci_draft.md").read_text(encoding="utf-8").lower()
    # KCI uses Korean for the disclaimer; SSCI uses English.
    assert "예측" in text_kci or "예측치안" in text_kci
    assert "predict" in text_ssci
