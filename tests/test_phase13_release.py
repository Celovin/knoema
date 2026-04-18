from __future__ import annotations

import tomllib
from pathlib import Path


def test_phase13_release_files_exist() -> None:
    expected = [
        Path("Dockerfile"),
        Path(".dockerignore"),
        Path("RELEASE.md"),
        Path(".github/workflows/release.yml"),
    ]

    for path in expected:
        assert path.exists(), path


def test_phase13_release_extra_includes_build_tools() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    release_deps = pyproject["project"]["optional-dependencies"]["release"]

    assert any(dep.startswith("build>=") for dep in release_deps)
    assert any(dep.startswith("twine>=") for dep in release_deps)


def test_phase13_release_workflow_uses_tag_gated_trusted_publishing() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "tags:" in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "PYPI_TOKEN" not in workflow
    assert "twine upload" not in workflow
    assert "twine check dist/*" in workflow
