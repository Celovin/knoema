from __future__ import annotations

from pathlib import Path


def test_phase14_tutorial_blog_draft_is_publish_ready() -> None:
    text = Path("docs/tutorial_blog.md").read_text(encoding="utf-8")

    required_sections = [
        "# Build a Persistent-Agent Simulation with Luvoire",
        "## 2. Run a YAML Simulation",
        "## 3. Inspect Logs in the Dashboard",
        "## 4. Use Memory Retrieval Diagnostics",
        "## Publishing Checklist",
    ]

    assert all(section in text for section in required_sections)
    assert "luvoire run examples/cli_dorm.yaml" in text
    assert "streamlit run dashboard/app.py" in text
    assert "retrieve_with_scores" in text
    assert "TODO" not in text
