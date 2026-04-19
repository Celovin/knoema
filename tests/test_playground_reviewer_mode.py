from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_subtask38_head_syncs_reviewer_query_param() -> None:
    assert "reviewer-mode-toggle" in playground_app.APP_HEAD
    assert "reviewer" in playground_app.APP_HEAD
    assert "URLSearchParams" in playground_app.APP_HEAD


def test_subtask38_render_outputs_sanitize_agent_identifiers() -> None:
    jsonl_text = "\n".join(
        [
            json.dumps(
                {
                    "tick": 0,
                    "agent_id": "agent_1",
                    "action_type": "speak",
                    "target": "agent_2",
                    "content": "agent_1 greets agent_2",
                }
            ),
            json.dumps(
                {
                    "tick": 1,
                    "agent_id": "agent_2",
                    "action_type": "accept",
                    "target": "agent_1",
                    "content": "agent_2 accepts",
                }
            ),
        ]
    )
    result = SimpleNamespace(
        agent_count=2,
        tick_count=2,
        log_count=2,
        action_breakdown={"agent_1": {"speak": 1}, "agent_2": {"accept": 1}},
        memory_snapshot={
            "agent_1": {"short_term": [{"content": "agent_1 remembers agent_2"}], "long_term": [], "monologue": []},
            "agent_2": {"short_term": [], "long_term": [], "monologue": []},
        },
        relationship_rows=[
            {
                "source": "agent_1",
                "target": "agent_2",
                "relationship_type": "peer",
                "weight": 0.6,
                "trust": 0.8,
                "familiarity": 0.4,
            }
        ],
        jsonl=jsonl_text,
        timeline_markdown="agent_1 meets agent_2",
        monologue_markdown="agent_1 thinks about agent_2",
        plan_markdown="agent_2 plans a reply",
        download_path="ignored.jsonl",
        batch_result=None,
    )

    outputs = playground_app._render_result_outputs(
        result,
        mode_label="Replay only",
        provider="Replay only",
        api_key="",
        language="en",
        reviewer_mode=True,
    )

    sanitized_jsonl = outputs[5]
    sanitized_summary = outputs[7]
    download_path = Path(outputs[6])

    try:
        assert "agent_1" not in sanitized_jsonl
        assert "agent_2" not in sanitized_jsonl
        assert "Agent A" in sanitized_jsonl
        assert "Agent B" in sanitized_jsonl
        assert "agent_1" not in sanitized_summary
        assert "agent_2" not in sanitized_summary
        assert "Agent A" in sanitized_summary
        assert outputs[12]["value"] == ["Agent A"]
        assert "Agent A" in download_path.read_text(encoding="utf-8")
    finally:
        download_path.unlink(missing_ok=True)
