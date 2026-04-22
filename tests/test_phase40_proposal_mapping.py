from __future__ import annotations

from pathlib import Path


def test_phase40_proposal_mapping_exists_and_declares_audit_scope() -> None:
    mapping = Path("docs/research/proposal_mapping.md").read_text(encoding="utf-8")

    assert "Proposal-to-Implementation Mapping" in mapping
    assert "planning/본문1_연구개발계획서_초안.md" in mapping
    assert "planning/codex_task_playground_layout.md" in mapping
    assert "planning/codex_execution_state.md" in mapping


def test_phase40_proposal_mapping_covers_required_proposal_lanes() -> None:
    mapping = Path("docs/research/proposal_mapping.md").read_text(encoding="utf-8")

    required_rows = [
        "Core engine runtime",
        "Application A: synthetic public-safety research",
        "Application B: game NPC tooling",
        "Application C: academic SaaS and reproducibility",
        "Benchmarks and validation",
        "Safety, accessibility, and compliance",
    ]

    missing = [row for row in required_rows if row not in mapping]

    assert missing == []


def test_phase40_proposal_mapping_references_files_and_tests() -> None:
    mapping = Path("docs/research/proposal_mapping.md").read_text(encoding="utf-8")

    assert "src/luvoire/memory/multi_layer.py" in mapping
    assert "playground/app.py" in mapping
    assert "tests/test_playground_advanced_research_gate.py" in mapping
    assert "tests/test_phase43_theory_of_mind.py" in mapping
