from __future__ import annotations

from pathlib import Path

README_FILES = [
    Path("README.md"),
    Path("README.ko.md"),
    Path("README.ja.md"),
    Path("README.zh-CN.md"),
    Path("README.zh-TW.md"),
    Path("README.de.md"),
    Path("README.fr.md"),
    Path("README.es.md"),
]


def test_phase38_all_readme_variants_exist() -> None:
    for path in README_FILES:
        assert path.exists(), path


def test_phase38_main_readme_exposes_language_selector() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Languages" in readme
    for path in README_FILES:
        assert f"({path.name})" in readme


def test_phase38_localized_readmes_link_back_to_full_english_reference() -> None:
    for path in README_FILES[1:]:
        text = path.read_text(encoding="utf-8")

        assert "[English](README.md)" in text
        assert "pip install -e " in text
        assert "Luvoire Playground" in text
