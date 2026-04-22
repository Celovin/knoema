from __future__ import annotations

import json
from pathlib import Path

from luvoire.export import (
    export_finetuning_jsonl,
    to_anthropic_jsonl,
    to_dpo_pairs,
    to_openai_jsonl,
    write_finetuning_jsonl,
)


def _sample_jsonl() -> str:
    rows = [
        {
            "tick": 0,
            "timestamp": "2026-04-21T09:00:00",
            "agent_id": "mina",
            "action": {
                "action_type": "speak",
                "target": "joon",
                "content": "Shares the plan.",
                "location": "Dorm",
            },
        },
        {
            "tick": 0,
            "timestamp": "2026-04-21T09:00:00",
            "agent_id": "joon",
            "action": {
                "action_type": "observe",
                "target": None,
                "content": "Reads the room.",
                "location": "Dorm",
            },
        },
    ]
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def test_batch_aa_openai_export_uses_chat_messages() -> None:
    records = to_openai_jsonl(_sample_jsonl())

    assert len(records) == 2
    assert [message["role"] for message in records[0]["messages"]] == [
        "system",
        "user",
        "assistant",
    ]
    assistant_payload = json.loads(records[0]["messages"][2]["content"])
    assert assistant_payload == {
        "action_type": "speak",
        "content": "Shares the plan.",
        "location": "Dorm",
        "target": "joon",
    }
    assert records[0]["metadata"]["agent_id"] == "mina"
    assert records[0]["metadata"]["action_type"] == "speak"


def test_batch_aa_anthropic_export_uses_system_plus_messages() -> None:
    records = to_anthropic_jsonl(_sample_jsonl())

    assert len(records) == 2
    assert "Luvoire simulation agent" in records[0]["system"]
    assert records[0]["messages"][0]["role"] == "user"
    assert records[0]["messages"][1]["role"] == "assistant"


def test_batch_aa_dpo_pairs_match_tick_and_agent() -> None:
    rejected = _sample_jsonl().replace("Shares the plan.", "Ignores the room.")

    pairs = to_dpo_pairs(_sample_jsonl(), rejected)

    assert len(pairs) == 1
    assert pairs[0]["metadata"]["agent_id"] == "mina"
    assert pairs[0]["chosen"][0]["role"] == "assistant"
    assert "Shares the plan." in pairs[0]["chosen"][0]["content"]
    assert "Ignores the room." in pairs[0]["rejected"][0]["content"]


def test_batch_aa_export_jsonl_and_writer(tmp_path: Path) -> None:
    output_path = tmp_path / "openai.jsonl"

    text = export_finetuning_jsonl(_sample_jsonl(), "openai")
    written = write_finetuning_jsonl(_sample_jsonl(), output_path, "anthropic")

    assert len(text.splitlines()) == 2
    assert json.loads(text.splitlines()[0])["messages"][2]["role"] == "assistant"
    assert written == output_path
    assert json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])["system"]
