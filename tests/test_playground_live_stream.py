from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask18_build_app_exposes_live_stream_toggle() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    live_streaming = next(
        component
        for component in components
        if type(component).__name__ == "Checkbox"
        and getattr(component, "elem_id", None) == "live-streaming-checkbox"
    )

    assert live_streaming.label == playground_app.LABELS["ko"]["live_streaming"]


def test_subtask18_wrapper_falls_back_to_batch_run_when_streaming_off(monkeypatch) -> None:
    monkeypatch.setattr(
        playground_app,
        "_run_with_player_mode",
        lambda *args: tuple(f"slot-{index}" for index in range(21)),
    )

    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    ]
    updates = list(
        playground_app._run_with_optional_streaming(
            False,
            "Dorm: two agents",
            "university_dorm_evening",
            "",
            "Replay only",
            "",
            "",
            "Mina",
            24,
            *trait_values,
            False,
            3,
            2,
            2,
            False,
            10,
            20260419,
            "English",
            "",
            "",
        )
    )

    assert len(updates) == 1
    assert len(updates[0]) == 21
    assert updates[0][0] == "slot-0"


def test_subtask18_live_stream_yields_multiple_tick_updates() -> None:
    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
        ]

    updates = list(
        playground_app._run_with_optional_streaming(
            True,
            "Dorm: two agents",
            "university_dorm_evening",
            "",
            "Replay only",
            "",
            "",
            "Mina",
            24,
            *trait_values,
            False,
            3,
            2,
            2,
            False,
            10,
            20260419,
            "English",
            "",
            "",
        )
    )

    assert len(updates) >= 2
    assert len(updates[-1]) == 21
    assert updates[-1][7].startswith("Mode: Replay only")
    assert updates[-1][5]
