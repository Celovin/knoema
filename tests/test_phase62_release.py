from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

import knoema
from knoema.api.server import create_app

RELEASE_VERSION = "0.2.0"
RELEASE_TAG = "v0.2.0"


def test_phase62_package_and_metadata_versions_are_synchronized() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load(Path("CITATION.cff").read_text(encoding="utf-8"))
    zenodo = json.loads(Path(".zenodo.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(".release-please-manifest.json").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == RELEASE_VERSION
    assert knoema.__version__ == RELEASE_VERSION
    assert create_app().version == RELEASE_VERSION
    assert citation["version"] == RELEASE_VERSION
    assert zenodo["version"] == RELEASE_VERSION
    assert manifest["."] == RELEASE_VERSION


def test_phase62_changelog_promotes_unreleased_notes() -> None:
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    unreleased_start = changelog.index("## [Unreleased]")
    release_start = changelog.index(f"## [{RELEASE_VERSION}] - 2026-04-19")
    release_end = changelog.index("## [0.1.1]")
    unreleased_section = changelog[unreleased_start:release_start]
    release_section = changelog[release_start:release_end]

    assert "Phase 61" not in unreleased_section
    assert "Phase 43 persona opt-in Theory of Mind" in release_section
    assert "Phase 61 interactive 5-chapter tutorial website" in release_section
    assert "### Security" in release_section
    assert "Phase 53 red-team safety suite" in release_section


def test_phase62_release_docs_surface_current_version_and_doi() -> None:
    for readme_path in sorted(Path(".").glob("README*.md")):
        readme = readme_path.read_text(encoding="utf-8")
        assert f"## Current version\n\n{RELEASE_VERSION}" in readme

    release = Path("RELEASE.md").read_text(encoding="utf-8")
    indexing = Path("docs/research/academic-indexing.md").read_text(encoding="utf-8")
    paper = Path("paper/main.tex").read_text(encoding="utf-8")

    assert f"git tag {RELEASE_TAG}" in release
    assert f"Release | `{RELEASE_TAG}`" in indexing
    assert "v0.2.0 DOI | Wired: `10.5281/zenodo.19645166`" in indexing
    assert r"\textbf{Software version:} \knoemaversion" in paper
    assert r"\newcommand{\knoemaversion}{0.2.0}" in paper
