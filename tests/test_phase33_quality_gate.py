from __future__ import annotations

from pathlib import Path


def test_phase33_ci_enforces_ninety_percent_coverage_gate() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "pytest --cov-fail-under=90" in workflow


def test_phase33_dev_dependency_includes_property_test_runner() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "hypothesis>=6.100" in pyproject
