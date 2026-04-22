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


def test_subtask52_build_app_exposes_theme_mode_toggle() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    theme_mode = next(
        component
        for component in components
        if type(component).__name__ == "Radio"
        and getattr(component, "elem_id", None) == "theme-mode-radio"
    )

    assert theme_mode.label == playground_app.LABELS["ko"]["theme"]
    expected_values = [
        choice[1] if isinstance(choice, tuple) else choice
        for choice in playground_app._theme_choices("ko")
    ]
    actual_values = [
        choice[1] if isinstance(choice, tuple) else choice
        for choice in theme_mode.choices
    ]
    assert actual_values == expected_values


def test_subtask52_theme_head_and_css_define_persistent_theme_system() -> None:
    assert playground_app.THEME_STORAGE_KEY in playground_app.APP_HEAD
    assert "prefers-color-scheme: dark" in playground_app.APP_HEAD
    assert "setFromLabel" in playground_app.APP_HEAD
    assert "--luvoire-bg" in playground_app.FOOTER_CSS
    assert 'data-luvoire-theme="dark"' in playground_app.FOOTER_CSS


def test_subtask52_theme_helpers_round_trip_localized_modes() -> None:
    assert playground_app._normalize_theme_mode(playground_app.LABELS["ko"]["theme_dark"]) == "dark"
    assert playground_app._normalize_theme_mode(playground_app.LABELS["en"]["theme_light"]) == "light"
    assert playground_app._theme_label("auto", "ko") == playground_app.LABELS["ko"]["theme_auto"]
    assert playground_app._theme_label("dark", "en") == playground_app.LABELS["en"]["theme_dark"]


def test_subtask65_light_mode_css_covers_high_risk_gradio_components() -> None:
    for selector in (
        ".gr-accordion",
        "[role=\"tabpanel\"]",
        ".gr-file",
        ".gr-code",
        ".gr-dropdown",
        ".gr-slider",
        "input[type=\"range\"]",
        ".cm-editor",
    ):
        assert selector in playground_app.FOOTER_CSS
