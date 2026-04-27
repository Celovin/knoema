"""Smoke tests for the ASC 2026 poster panel generator."""

from __future__ import annotations

from pathlib import Path

POSTER_DIR = Path(__file__).resolve().parents[1] / "paper" / "asc2026_poster"


def test_four_panel_pdfs_present() -> None:
    expected = {
        "panel_method_3tier.pdf",
        "panel_theory_rat.pdf",
        "panel_sensitivity_sobol.pdf",
        "panel_replay_hash.pdf",
    }
    files = {p.name for p in POSTER_DIR.iterdir()}
    missing = expected - files
    assert not missing, f"missing panels: {sorted(missing)}"


def test_four_panel_svgs_present() -> None:
    expected = {
        "panel_method_3tier.svg",
        "panel_theory_rat.svg",
        "panel_sensitivity_sobol.svg",
        "panel_replay_hash.svg",
    }
    files = {p.name for p in POSTER_DIR.iterdir()}
    missing = expected - files
    assert not missing, f"missing SVGs: {sorted(missing)}"


def test_pdf_panels_are_nonempty() -> None:
    for name in (
        "panel_method_3tier.pdf",
        "panel_theory_rat.pdf",
        "panel_sensitivity_sobol.pdf",
        "panel_replay_hash.pdf",
    ):
        path = POSTER_DIR / name
        assert path.stat().st_size > 1024, f"{name} looks empty"


def test_build_panels_module_imports() -> None:
    import paper.asc2026_poster.build_panels as build_panels

    assert callable(build_panels.panel_method_3tier)
    assert callable(build_panels.panel_theory_rat)
    assert callable(build_panels.panel_sensitivity_sobol)
    assert callable(build_panels.panel_replay_hash)


def test_pdf_panels_are_byte_deterministic_across_reruns() -> None:
    """Panels reproduce byte-identical PDFs after the savefig metadata fix."""

    import hashlib
    import importlib

    import paper.asc2026_poster.build_panels as build_panels

    pdf_names = [
        "panel_method_3tier.pdf",
        "panel_theory_rat.pdf",
        "panel_sensitivity_sobol.pdf",
        "panel_replay_hash.pdf",
    ]
    importlib.reload(build_panels)
    build_panels.main()
    first = {
        name: hashlib.sha256((POSTER_DIR / name).read_bytes()).hexdigest()
        for name in pdf_names
    }
    importlib.reload(build_panels)
    build_panels.main()
    second = {
        name: hashlib.sha256((POSTER_DIR / name).read_bytes()).hexdigest()
        for name in pdf_names
    }
    assert first == second, (
        "panels are not byte-deterministic across reruns; "
        "check savefig metadata stripping"
    )
