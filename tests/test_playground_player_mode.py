from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask33_build_app_exposes_player_mode_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    provider = next(
        component
        for component in components
        if type(component).__name__ == "Radio"
        and getattr(component, "elem_id", None) == "mode-radio"
    )
    player_panel = next(
        component
        for component in components
        if type(component).__name__ == "Column"
        and getattr(component, "elem_id", None) == "player-mode-panel"
    )
    player_input = next(
        component
        for component in components
        if type(component).__name__ == "Textbox"
        and getattr(component, "elem_id", None) == "player-input"
    )

    provider_values = [choice[1] if isinstance(choice, tuple) else choice for choice in provider.choices]
    provider_display_labels = [choice[0] if isinstance(choice, tuple) else choice for choice in provider.choices]
    assert "Player mode" in provider_values
    assert playground_app.LABELS["ko"]["player_mode"] in provider_display_labels
    assert player_panel.visible is False
    assert player_input.label == playground_app.LABELS["ko"]["player_input"]


def test_subtask48_build_app_exposes_voice_mode_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    stt_engine = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "player-stt-engine"
    )
    tts_engine = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "player-tts-engine"
    )
    voice_input = next(
        component
        for component in components
        if type(component).__name__ == "Audio"
        and getattr(component, "elem_id", None) == "player-voice-input"
    )
    voice_output = next(
        component
        for component in components
        if type(component).__name__ == "Audio"
        and getattr(component, "elem_id", None) == "player-voice-output"
    )

    assert stt_engine.label == playground_app.LABELS["ko"]["player_stt_engine"]
    assert tts_engine.label == playground_app.LABELS["ko"]["player_tts_engine"]
    assert voice_input.label == playground_app.LABELS["ko"]["player_voice_input"]
    assert voice_output.label == playground_app.LABELS["ko"]["player_voice_output"]


def test_subtask33_player_session_advances_tick_with_player_action() -> None:
    trait_defaults = {
        field_name: playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    }

    session, initial_result, initial_status = playground_simulation.start_player_session(
        scenario_name="Dorm: two agents",
        primary_name="Customer",
        primary_age=28,
        personality_overrides=trait_defaults,
        ticks=2,
        agent_count=2,
        agent_overrides=[
            {
                "name": "Customer",
                "age": 28,
                "personality_overrides": trait_defaults,
            },
            {
                "name": "Bjorn",
                "age": 34,
                "personality_overrides": trait_defaults,
                "routine_text": playground_simulation.routine_preset_text("shopkeeper"),
            },
        ],
        primary_planning_enabled=False,
        planning_depth=3,
        language="ko",
    )

    updated_session, result, status = playground_simulation.advance_player_session(
        session,
        "Bjorn에게 맥주 1개 주문",
    )

    assert session["player_name"] == "Customer"
    assert initial_result.tick_count == 0
    assert "기다리" in initial_status
    assert updated_session is not None
    assert len(updated_session["player_actions"]) == 1
    assert result is not None
    assert "기다리" in status

    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert len(rows) == 2
    player_rows = [
        row
        for row in rows
        if row["action"]["metadata"].get("player_mode") is True
    ]
    npc_rows = [row for row in rows if row["agent_id"] != session["player_agent_id"]]

    assert len(player_rows) == 1
    assert player_rows[0]["action"]["action_type"] == "speak"
    assert player_rows[0]["action"]["target"] != session["player_agent_id"]
    assert player_rows[0]["action"]["target"] == npc_rows[0]["agent_id"]
    assert npc_rows


def test_subtask33_run_wrapper_starts_player_mode_session(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_start_player_session(**kwargs: object) -> tuple[dict[str, object], SimpleNamespace, str]:
        captured.update(kwargs)
        return (
            {"player_agent_id": "agent_1", "language": "en"},
            SimpleNamespace(
                mode="Replay only",
                relationship_rows=[],
                timeline_markdown="### Timeline",
                monologue_markdown="t0",
                plan_markdown="### Current plan",
                action_breakdown={"agent_1": {"speak": 1}},
                memory_snapshot={},
                jsonl="{}",
                download_path="C:\\temp\\playground.jsonl",
                agent_count=2,
                tick_count=0,
                log_count=0,
                batch_result=None,
            ),
            "Awaiting input",
        )

    monkeypatch.setattr(playground_app, "start_player_session", fake_start_player_session)

    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    ]

    outputs = playground_app._run_with_player_mode(
        "Dorm: two agents",
        "university_dorm_evening",
        "",
        "Player mode",
        "",
        "",
        "Customer",
        28,
        *trait_values,
        False,
        3,
        2,
        2,
        False,
        10,
        20260419,
        "English",
    )

    assert len(outputs) == 21
    assert outputs[7].startswith("Mode: Player mode")
    assert outputs[-1] == "Awaiting input"
    assert captured["scenario_name"] == "Dorm: two agents"
    assert captured["primary_name"] == "Customer"


def test_subtask48_advance_player_mode_uses_stt_and_tts(monkeypatch) -> None:
    session = {"language": "en", "player_agent_id": "player-1"}
    result = SimpleNamespace(jsonl="{}")

    monkeypatch.setattr(
        playground_app,
        "_render_result_outputs",
        lambda *args, **kwargs: tuple(f"slot-{index}" for index in range(18)),
    )
    monkeypatch.setattr(
        playground_app,
        "transcribe_player_audio",
        lambda audio_path, *, engine, language: ("Ask Bjorn for one beer", "Voice input transcribed."),
    )
    monkeypatch.setattr(
        playground_app,
        "advance_player_session",
        lambda current_session, player_text: (current_session, result, "Awaiting input"),
    )
    monkeypatch.setattr(
        playground_app,
        "_latest_npc_response_text",
        lambda current_result, current_session: "Bjorn nods and starts pouring.",
    )
    monkeypatch.setattr(
        playground_app,
        "synthesize_text_to_audio",
        lambda text, *, engine, language: ("C:\\temp\\reply.wav", "Audio response is ready."),
    )

    outputs = playground_app._advance_player_mode(
        session,
        "",
        "C:\\temp\\voice.wav",
        "whisper_cpp",
        "pyttsx3",
    )

    assert len(outputs) == 22
    assert outputs[18]["value"] == "C:\\temp\\reply.wav"
    assert "Voice input transcribed." in outputs[20]
    assert "Audio response is ready." in outputs[20]
    assert outputs[21]["value"] == ""
