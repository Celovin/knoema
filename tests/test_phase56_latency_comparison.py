from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("benchmarks/formal_report")


def test_phase56_latency_comparison_file_has_measured_and_published_rows() -> None:
    payload = json.loads((ROOT / "results/latency_comparison.json").read_text(encoding="utf-8"))

    measured = {row["path_id"]: row for row in payload["measured_rows"]}
    published = {row["reference_id"]: row for row in payload["published_rows"]}

    assert set(measured) == {"playground_replay", "playground_openai"}
    assert set(published) == {
        "nvidia_ace_target",
        "inworld_tts_1",
        "inworld_tts_1_5",
        "inworld_runtime_guidance",
    }
    assert measured["playground_replay"]["mean_tick_latency_ms"] < 200.0
    assert measured["playground_openai"]["mean_tick_latency_ms"] > 1000.0
    assert published["nvidia_ace_target"]["latency_ms_high"] == 200.0
    assert published["inworld_runtime_guidance"]["latency_ms_high"] == 3000.0


def test_phase56_latency_sources_stay_official_and_vendor_specific() -> None:
    payload = json.loads((ROOT / "results/latency_comparison.json").read_text(encoding="utf-8"))

    urls = [
        source["url"]
        for row in payload["published_rows"]
        for source in row["sources"]
    ]

    assert any(url.startswith("https://developer.nvidia.com/") for url in urls)
    assert any(url.startswith("https://docs.nvidia.com/") for url in urls)
    assert any(url.startswith("https://inworld.ai/") for url in urls)
    assert any(url.startswith("https://community.inworld.ai/") for url in urls)


def test_phase56_summary_and_report_include_latency_comparison() -> None:
    summary = (ROOT / "results/summary.md").read_text(encoding="utf-8")

    assert "Knoema Playground replay-only" in summary
    assert "Knoema Playground OpenAI mode" in summary
    assert "NVIDIA ACE target envelope" in summary
    assert "Inworld TTS-1.5 first audio chunk" in summary
    assert (ROOT / "report.pdf").exists()
