from __future__ import annotations

from pathlib import Path

from scripts.check_gradio_compat import find_compatibility_issues


def test_gradio_compat_guard_rejects_unsupported_launch_keywords() -> None:
    source = """
import gradio as gr

demo = gr.Blocks()
demo.launch(css="body { color: red; }")
"""

    issues = find_compatibility_issues(source)

    assert issues
    assert issues[0].keyword == "css"


def test_gradio_compat_guard_accepts_current_playground_app() -> None:
    source = Path("playground/app.py").read_text(encoding="utf-8")

    assert find_compatibility_issues(source) == []
