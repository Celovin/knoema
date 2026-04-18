from __future__ import annotations

import re
from pathlib import Path


def test_phase30_arxiv_v2_sources_exist() -> None:
    expected = [
        "paper/main.tex",
        "paper/abstract.tex",
        "paper/appendix.tex",
        "paper/sections/01_introduction.tex",
        "paper/sections/02_related_work.tex",
        "paper/sections/03_architecture.tex",
        "paper/sections/04_experiments.tex",
        "paper/sections/05_applications.tex",
        "paper/sections/06_discussion.tex",
        "paper/sections/07_conclusion.tex",
        "paper/tables/benchmark_summary.tex",
        "paper/tables/release_artifacts.tex",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []
    assert len(list(Path("paper/figures").glob("*.tex"))) >= 10


def test_phase30_main_uses_arxiv_v2_structure() -> None:
    main = Path("paper/main.tex").read_text(encoding="utf-8")

    assert "Persistent NPCs" in main
    assert "\\input{abstract}" in main
    assert "\\input{sections/01_introduction}" in main
    assert "\\input{sections/05_applications}" in main
    assert "\\appendix" in main
    assert "\\input{appendix}" in main
    assert "\\nocite{*}" in main


def test_phase30_paper_includes_results_and_safety_boundary() -> None:
    body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            Path("paper/abstract.tex"),
            Path("paper/sections/04_experiments.tex"),
            Path("paper/sections/06_discussion.tex"),
            Path("paper/sections/05_applications.tex"),
        ]
    )

    assert "50-agent" in body
    assert "2,100 committed actions" in body
    assert "p=0.000244" in body
    assert "fictional, synthetic, and non-identifying" in body
    assert "not designed for prediction" in body


def test_phase30_references_are_expanded_for_preprint() -> None:
    references = Path("paper/references.bib").read_text(encoding="utf-8")
    entries = re.findall(r"^@", references, flags=re.MULTILINE)

    assert len(entries) >= 50
    assert "park2023generative" in references
    assert "wu2023autogen" in references
    assert "lewis2020rag" in references
    assert "sandve2013tenrules" in references
    assert "gebreu" not in references.lower()
