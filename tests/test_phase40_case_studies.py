from __future__ import annotations

from pathlib import Path

CASE_STUDIES = [
    Path("docs/case_studies/01_knot_episode_1_integration.md"),
    Path("docs/case_studies/02_korean_university_pilot.md"),
    Path("docs/case_studies/03_indie_studio_adoption.md"),
]


def test_phase40_case_studies_exist() -> None:
    for path in CASE_STUDIES:
        assert path.exists(), path


def test_phase40_case_studies_share_required_sections() -> None:
    required_sections = [
        "## Executive Summary",
        "## Background",
        "## Solution Design",
        "## Timeline",
        "## Projected Metrics",
        "## Success Metrics",
        "## Risks and Guardrails",
    ]

    for path in CASE_STUDIES:
        text = path.read_text(encoding="utf-8")
        assert "Hypothetical case study." in text
        for section in required_sections:
            assert section in text, f"{path}: missing {section}"


def test_phase40_docs_navigation_includes_case_studies() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    for path in CASE_STUDIES:
        assert path.as_posix() in readme
        assert path.as_posix().removeprefix("docs/") in docs_index
        assert path.as_posix().removeprefix("docs/") in mkdocs
