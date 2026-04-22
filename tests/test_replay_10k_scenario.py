from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import msgpack  # type: ignore[import-untyped]
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT / "demo" / "replay"
VIEWER_PATH = REPLAY_DIR / "viewer.html"
TEN_K_REPLAY = REPLAY_DIR / "replay_10000agents_gangnam_7pm.msgpack"
FIVE_K_REPLAY = REPLAY_DIR / "replay_5000agents_gangnam_7pm.msgpack"
SCENARIO_60X60 = REPLAY_DIR / "scenario_config_60x60.yaml"
FORECAST_UPPER_BOUND_BYTES = 10_500_000
REPLAY_SHA256_BASELINES = {
    "replay_100agents_gangnam_7pm.msgpack": (
        "8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab"
    ),
    "replay_1000agents_gangnam_7pm.msgpack": (
        "0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b"
    ),
    "replay_5000agents_gangnam_7pm.msgpack": (
        "d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01"
    ),
}
FORBIDDEN_STRINGS = (
    "Lith" + "eon",
    "Se" + "izn",
    "Ov" + "riel",
    "Fang" + "den",
    "Not" + "rivo",
    "Milky" + "pix",
    "Ya" + "mi",
    "Qwen" + "3.5-35B-A3B",
)


def test_10k_replay_regeneration_is_byte_identical(tmp_path: Path) -> None:
    hashes = []
    for index in range(3):
        output_dir = tmp_path / f"run_{index}"
        subprocess.run(
            [
                sys.executable,
                "demo/replay/generate_replay.py",
                "--scenario",
                "10k",
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            check=True,
        )
        hashes.append(_sha256(output_dir / TEN_K_REPLAY.name))

    assert len(set(hashes)) == 1


def test_10k_replay_size_and_format_parity() -> None:
    assert TEN_K_REPLAY.stat().st_size <= FORECAST_UPPER_BOUND_BYTES

    five_k = _unpack(FIVE_K_REPLAY)
    ten_k = _unpack(TEN_K_REPLAY)
    assert list(ten_k) == list(five_k)
    assert ten_k["metadata"]["agent_count"] == 10000
    assert ten_k["metadata"]["tick_count"] == 30
    assert ten_k["metadata"]["grid_bounds"] == {"width": 60, "height": 60}
    assert len(ten_k["agents"]) == 10000
    assert len(ten_k["frames"]) == 30


def test_scenario_60x60_has_no_forbidden_entity_strings() -> None:
    text = SCENARIO_60X60.read_text(encoding="utf-8")
    assert not [forbidden for forbidden in FORBIDDEN_STRINGS if forbidden in text]


def test_existing_100_1k_and_5k_replays_match_committed_sha256() -> None:
    for filename, expected_sha256 in REPLAY_SHA256_BASELINES.items():
        assert _sha256(REPLAY_DIR / filename) == expected_sha256


def test_replay_viewer_loads_and_plays_10k_from_file_url() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(VIEWER_PATH.as_uri(), wait_until="domcontentloaded")
            page.wait_for_function("() => !document.querySelector('#scenario').disabled")
            page.select_option("#scenario", TEN_K_REPLAY.name)
            page.locator("#file-input").set_input_files(TEN_K_REPLAY)
            page.wait_for_function(
                "() => document.querySelector('#status').textContent.includes('10000 agents loaded')",
                timeout=5000,
            )
            assert page.locator("#scrubber").get_attribute("max") == "29"

            page.select_option("#speed", "20")
            page.locator("#play").click()
            elapsed_ms = page.evaluate(
                """() => new Promise((resolve, reject) => {
                    const started = performance.now();
                    const scrubber = document.querySelector("#scrubber");
                    const timer = setInterval(() => {
                      if (Number(scrubber.value) >= 29) {
                        clearInterval(timer);
                        resolve(performance.now() - started);
                      }
                      if (performance.now() - started > 120000) {
                        clearInterval(timer);
                        reject(new Error("10K replay did not reach final tick within 120 seconds"));
                      }
                    }, 10);
                })"""
            )
            assert float(elapsed_ms) < 120_000
        finally:
            browser.close()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unpack(path: Path) -> dict[str, object]:
    return msgpack.unpackb(path.read_bytes(), raw=False)
