from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask60_caveat_helper_covers_cjk_languages_only() -> None:
    assert "Ashton" in playground_app._honesty_humility_caveat_markdown("한국어")
    assert "Ashton" in playground_app._honesty_humility_caveat_markdown("日本語")
    assert "Ashton" in playground_app._honesty_humility_caveat_markdown("中文")
    assert playground_app._honesty_humility_caveat_markdown("English") == ""


def test_subtask60_build_app_renders_honesty_humility_caveat_banner() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    caveats = [
        component
        for component in components
        if getattr(component, "elem_id", None) == "honesty-humility-caveat"
    ]

    assert len(caveats) == 1
    assert caveats[0].visible is True
    assert "Ashton" in str(getattr(caveats[0], "value", ""))


def test_subtask60_caveat_update_hides_banner_for_english() -> None:
    korean_update = playground_app._honesty_humility_caveat_update("한국어")
    english_update = playground_app._honesty_humility_caveat_update("English")

    assert korean_update["visible"] is True
    assert "Ashton" in korean_update["value"]
    assert english_update["visible"] is False
    assert english_update["value"] == ""
