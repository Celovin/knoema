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


# --- Audit-3 hardening: Tier A code-ref import resolution -------------


def test_lint_flags_tier_a_ref_to_unimportable_module(tmp_path: Path) -> None:
    """A Tier A ref pointing to a non-existent dotted module must be
    rejected by the linter (not just regex-matched).
    """

    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  ghost:\n"
            "    tier: A\n"
            "    ref: code:luvoire.does.not.exist.v1\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("not importable" in issue for issue in issues)


def test_lint_flags_tier_a_ref_with_version_mismatch(tmp_path: Path) -> None:
    """Tier A ref ``...v9`` must fail when module.VERSION is ``v1``."""

    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  bad_version:\n"
            "    tier: A\n"
            "    ref: code:luvoire.theory.rat.v9\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("disagrees with module.VERSION" in issue for issue in issues)


def test_lint_flags_tier_a_ref_to_module_without_version(tmp_path: Path) -> None:
    """A module that exists but exposes no VERSION constant must be
    flagged so the convention stays enforced for new Tier A targets.
    Use a stable module that has no VERSION (``json`` from stdlib).
    """

    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  versionless:\n"
            "    tier: A\n"
            "    ref: code:json.v1\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("no VERSION constant" in issue for issue in issues)


def test_lint_flags_tier_a_ref_with_malformed_shape(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  malformed:\n"
            "    tier: A\n"
            "    ref: code:luvoire.theory.rat\n"
        ),
    )
    issues = lint_file(fixture)
    assert any("does not match" in issue for issue in issues)


def test_lint_accepts_tier_a_ref_with_aligned_version(tmp_path: Path) -> None:
    """Sanity — a properly-shaped, importable, VERSION-matching ref
    must NOT raise an issue (only the ``demographic_projection`` flag
    interlock would, and we only check ref resolution here).
    """

    fixture = _write(
        tmp_path / "scenario.yaml",
        (
            'schema_version: "2.0"\n'
            "parameters:\n"
            "  rat_threshold:\n"
            "    tier: A\n"
            "    ref: code:luvoire.theory.rat.v1\n"
        ),
    )
    issues = lint_file(fixture)
    # No ref-resolution issue should be raised; other tier-A checks may
    # still pass clean for this minimal fixture.
    ref_issues = [
        i for i in issues
        if "not importable" in i
        or "disagrees with module.VERSION" in i
        or "no VERSION constant" in i
        or "does not match" in i
    ]
    assert ref_issues == [], ref_issues
