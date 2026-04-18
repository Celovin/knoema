from __future__ import annotations

from pathlib import Path


def test_phase29_mkdocs_files_exist() -> None:
    expected = [
        "mkdocs.yml",
        "docs/index.md",
        "docs/getting-started/installation.md",
        "docs/getting-started/first-simulation.md",
        "docs/getting-started/configuration.md",
        "docs/api/persona.md",
        "docs/api/memory.md",
        "docs/api/relationship.md",
        "docs/api/environment.md",
        "docs/api/emotion.md",
        "docs/api/decision.md",
        "docs/api/simulator.md",
        "docs/api/llm-gateway.md",
        "docs/guides/game-integration.md",
        "docs/guides/research-workflow.md",
        "docs/guides/safety-scenarios.md",
        "docs/reference/cli.md",
        "docs/community/discord.md",
        "docs/community/contributing.md",
        "docs/community/roadmap.md",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase29_mkdocs_config_includes_api_reference() -> None:
    config = Path("mkdocs.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "mkdocstrings" in config
    assert "Getting Started:" in config
    assert "Core Concepts:" in config
    assert "API:" in config
    assert "Guides:" in config
    assert "SDK:" in config
    assert "Reports:" in config
    assert "Media:" in config
    assert "Blog Drafts:" in config
    assert "Community:" in config
    assert "mkdocs-material" in pyproject
    assert "mkdocstrings[python]" in pyproject


def test_phase29_docs_keep_safety_boundary_and_public_links() -> None:
    index = Path("docs/index.md").read_text(encoding="utf-8")
    safety = Path("docs/guides/safety-scenarios.md").read_text(encoding="utf-8")
    game = Path("docs/guides/game-integration.md").read_text(encoding="utf-8")
    research = Path("docs/guides/research-workflow.md").read_text(encoding="utf-8")

    assert "fictional, synthetic, and non-identifying" in index
    assert "Not Allowed" in safety
    assert "Prediction of future crime" in safety
    assert "GameSession" in game
    assert "config, seed, commit hash, logs, and summary metrics" in research


def test_phase29_mkdocs_nav_covers_all_public_markdown_pages() -> None:
    config = Path("mkdocs.yml").read_text(encoding="utf-8")
    docs_root = Path("docs")

    public_markdown_paths = sorted(
        path.relative_to(docs_root).as_posix()
        for path in docs_root.rglob("*.md")
    )

    for relative_path in public_markdown_paths:
        assert relative_path in config, relative_path
