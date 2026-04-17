from __future__ import annotations

from pathlib import Path


def test_phase12_paper_sources_exist() -> None:
    root = Path("paper")
    expected = [
        root / "main.tex",
        root / "references.bib",
        root / "build_pdf.py",
        root / "sections" / "abstract.tex",
        root / "sections" / "introduction.tex",
        root / "sections" / "related.tex",
        root / "sections" / "architecture.tex",
        root / "sections" / "implementation.tex",
        root / "sections" / "experiments.tex",
        root / "sections" / "safety.tex",
        root / "sections" / "conclusion.tex",
    ]

    for path in expected:
        assert path.exists(), path


def test_phase12_paper_has_required_citations_and_no_placeholders() -> None:
    main = Path("paper/main.tex").read_text(encoding="utf-8")
    bib = Path("paper/references.bib").read_text(encoding="utf-8")
    sections = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(Path("paper/sections").glob("*.tex"))
    )

    assert "\\bibliography{references}" in main
    assert "park2023generative" in bib
    assert "vezhnevets2023concordia" in bib
    assert "terhoeven2025mesa" in bib
    assert "TODO" not in main + bib + sections
    assert "placeholder" not in (main + bib + sections).lower()
