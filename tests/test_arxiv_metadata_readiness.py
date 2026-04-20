from __future__ import annotations

import re
from pathlib import Path


def test_phase65_paper_sources_have_no_placeholders_except_pending_arxiv_id() -> None:
    for relative_path in (
        Path("paper/main.tex"),
        Path("paper/abstract.txt"),
        Path("paper/references.bib"),
    ):
        text = relative_path.read_text(encoding="utf-8").replace("ARXIV_ID_PENDING", "")
        lowered = text.lower()
        assert "tbd" not in lowered
        assert "todo" not in lowered
        assert "placeholder" not in lowered


def test_phase65_readme_arxiv_badges_stay_pending_until_assignment() -> None:
    badge_pattern = re.compile(r"https://img\.shields\.io/badge/arXiv-([^)\]]+)")

    for relative_path in (Path("README.md"), Path("paper/README.md")):
        text = relative_path.read_text(encoding="utf-8")
        match = badge_pattern.search(text)
        assert match is not None, f"missing arXiv badge in {relative_path}"
        assert "ARXIV_ID_PENDING" in match.group(1)
