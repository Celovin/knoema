from __future__ import annotations

from pathlib import Path

from scripts.check_gradio_compat import find_compatibility_issues


def test_gradio_compat_guard_rejects_unsupported_launch_keywords() -> None:
    """The guard catches genuinely-invalid kwargs on ``.launch(...)``.

    Note: ``css`` / ``head`` migrated between ``Blocks`` and ``launch``
    in Gradio 6 and are accepted on both via ``**kwargs`` with a
    deprecation warning, so they no longer trigger the guard. We use
    an obviously-typo'd kwarg to ensure the guard still fires on real
    incompatibilities.
    """

    source = """
import gradio as gr

demo = gr.Blocks()
demo.launch(definitely_not_a_real_kwarg="oops")
"""

    issues = find_compatibility_issues(source)

    assert issues
    assert issues[0].keyword == "definitely_not_a_real_kwarg"


def test_gradio_compat_guard_accepts_current_playground_app() -> None:
    source = Path("playground/app.py").read_text(encoding="utf-8")

    assert find_compatibility_issues(source) == []
