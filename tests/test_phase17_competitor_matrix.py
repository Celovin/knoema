"""Phase 17 tests for the public competitor matrix."""

from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/competitor_matrix.md")


def test_phase17_competitor_matrix_exists_and_positions_knoema() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    assert "Knoema Only" in matrix
    assert "directed relationship graph" in matrix
    assert "Korean-capable prompt templates" in matrix
    assert "Godot plus Unity adapter scaffolds" in matrix


def test_phase17_competitor_matrix_covers_required_competitors() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    required = [
        "Stanford Generative Agents",
        "Google DeepMind Concordia",
        "Microsoft AutoGen",
        "OpenAI Swarm",
        "Inworld AI",
        "Convai",
        "Character.AI",
        "Mesa",
        "AnyLogic",
        "NetLogo",
    ]

    missing = [name for name in required if name not in matrix]

    assert missing == []


def test_phase17_competitor_matrix_keeps_public_sources() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    assert "https://arxiv.org/abs/2304.03442" in matrix
    assert "https://github.com/google-deepmind/concordia" in matrix
    assert "https://docs.convai.com/api-docs/plugins-and-integrations/unity-plugin" in matrix
    assert "https://mesa.readthedocs.io/stable/" in matrix
