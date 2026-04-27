"""Tests for scripts/lint_dsl_v2.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_dsl_v2 import lint_file, main


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_lint_skips_v1_scenarios(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "v1.yaml",
        'schema_version: "1.0"\nscenario_id: legacy\n',
    )
    assert lint_file(fixture) == []


def test_lint_passes_clean_v2_baseline() -> None:
    fixture = (
        Path(__file__).parent / "fixtures" / "scenarios" / "v2_rat_baseline.yaml"
    )
    assert lint_file(fixture) == []


def test_lint_flags_tier_a_with_inline_value(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  bad:\n"
            "    tier: A\n"
            "    ref: code:luvoire.theory.rat.v1\n"
            "    value: 0.5\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("Tier A must only define 'ref'" in issue for issue in issues)


def test_lint_flags_tier_b_without_source(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  prior:\n"
            "    tier: B\n"
            "    value: 0.5\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("Tier B requires 'source'" in issue for issue in issues)


def test_lint_flags_tier_c_without_range(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  knob:\n"
            "    tier: C\n"
            "    default: 0.5\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("Tier C requires 'range'" in issue for issue in issues)


def test_lint_flags_unknown_tier(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  weird:\n"
            "    tier: Q\n"
            "    value: 0.5\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("tier must be one of A/B/C" in issue for issue in issues)


def test_main_exit_zero_on_clean_baseline(capsys: pytest.CaptureFixture[str]) -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "scenarios"
    code = main([str(fixture_dir / "v2_rat_baseline.yaml"), "--strict"])
    assert code == 0


def test_main_exit_one_on_issue_strict(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  prior:\n"
            "    tier: B\n"
            "    value: 0.5\n"
        ),
    )
    code = main([str(fixture), "--strict"])
    assert code == 1
