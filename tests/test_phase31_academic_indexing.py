from __future__ import annotations

import json
from pathlib import Path

import yaml


def test_phase31_academic_indexing_files_exist() -> None:
    expected = [
        "CITATION.cff",
        ".zenodo.json",
        "docs/research/academic-indexing.md",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase31_citation_metadata_is_machine_readable() -> None:
    citation = yaml.safe_load(Path("CITATION.cff").read_text(encoding="utf-8"))

    assert citation["cff-version"] == "1.2.0"
    assert citation["type"] == "software"
    assert citation["version"] == "0.1.1"
    assert citation["license"] == "MIT"
    assert citation["repository-code"] == "https://github.com/Celovin/knoema"
    assert citation["authors"][0]["name"] == "Celovin"
    assert "preferred-citation" in citation


def test_phase31_zenodo_metadata_is_valid_json() -> None:
    metadata = json.loads(Path(".zenodo.json").read_text(encoding="utf-8"))

    assert metadata["upload_type"] == "software"
    assert metadata["access_right"] == "open"
    assert metadata["license"] == "mit"
    assert metadata["version"] == "0.1.1"
    assert metadata["creators"][0]["name"] == "Celovin"
    assert any(
        item["identifier"] == "https://github.com/Celovin/knoema"
        for item in metadata["related_identifiers"]
    )


def test_phase31_readme_and_docs_surface_indexing_status() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    docs = Path("docs/research/academic-indexing.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "zenodo.org/badge/DOI/10.5281/zenodo.19643410.svg" in readme
    assert "doi.org/10.5281/zenodo.19643410" in readme
    assert "Papers%20with%20Code-submission%20packet" in readme
    assert "10.5281/zenodo.19643410" in docs
    assert "Papers with Code entry | Pending external submission" in docs
    assert "Academic Indexing: research/academic-indexing.md" in mkdocs
