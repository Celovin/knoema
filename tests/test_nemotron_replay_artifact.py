from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import msgpack  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT / "demo" / "replay"
NEMOTRON_REPLAY = REPLAY_DIR / "replay_10000agents_nemotron_gangnam_7pm.msgpack"
NEMOTRON_SHA256 = "9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9"
NEMOTRON_REVISION = "0381f03a403df78a7998000f8b11705635b654fd"


def test_nemotron_10k_replay_metadata_size_and_sha() -> None:
    assert NEMOTRON_REPLAY.stat().st_size <= 25_000_000
    assert _sha256(NEMOTRON_REPLAY) == NEMOTRON_SHA256

    payload = msgpack.unpackb(NEMOTRON_REPLAY.read_bytes(), raw=False)

    assert payload["metadata"]["agent_count"] == 10000
    assert payload["metadata"]["persona_source"] == "nemotron"
    assert payload["metadata"]["persona_dataset_revision"] == NEMOTRON_REVISION
    assert payload["metadata"]["persona_dataset_repo_id"] == "nvidia/Nemotron-Personas-Korea"
    assert len(payload["agents"]) == 10000
    assert len(payload["frames"]) == 30
    assert payload["agents"][0]["demographics"]["region"] == "서울-강남구"


def test_nemotron_10k_verify_existing_cli_passes() -> None:
    subprocess.run(
        [
            sys.executable,
            "demo/replay/generate_replay.py",
            "--scenario",
            "10k",
            "--persona-source",
            "nemotron",
            "--verify-existing",
        ],
        cwd=ROOT,
        check=True,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
