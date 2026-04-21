from __future__ import annotations

import importlib
import json
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


def _sample_jsonl() -> str:
    row = {
        "tick": 1,
        "timestamp": "2026-04-21T09:30:00",
        "agent_id": "agent_1",
        "action": {
            "action_type": "comfort",
            "target": "agent_2",
            "content": "Keeps the group calm.",
            "location": "Lab",
        },
    }
    return json.dumps(row, sort_keys=True) + "\n"


def test_batch_aa_playground_exposes_finetuning_export_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    format_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "finetuning-format"
    )
    export_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "finetuning-export-button"
    )

    assert format_dropdown.label == playground_app.LABELS["ko"]["finetuning_format"]
    assert export_button.value == playground_app.LABELS["ko"]["finetuning_button"]


def test_batch_aa_playground_writes_finetuning_jsonl() -> None:
    export_path = Path(playground_app._export_finetuning_dataset(_sample_jsonl(), "openai", "English"))

    try:
        lines = export_path.read_text(encoding="utf-8").splitlines()
        payload = json.loads(lines[0])
        assert export_path.suffix == ".jsonl"
        assert payload["messages"][2]["role"] == "assistant"
        assert "Keeps the group calm." in payload["messages"][2]["content"]
    finally:
        export_path.unlink(missing_ok=True)
