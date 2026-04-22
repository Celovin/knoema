from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import msgpack  # type: ignore[import-untyped]
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT / "demo" / "replay"
VIEWER_PATH = REPLAY_DIR / "viewer.html"
FIVE_K_REPLAY = REPLAY_DIR / "replay_5000agents_gangnam_7pm.msgpack"
ONE_K_REPLAY = REPLAY_DIR / "replay_1000agents_gangnam_7pm.msgpack"
SCENARIO_40X40 = REPLAY_DIR / "scenario_config_40x40.yaml"
LEGACY_SHA_MANIFEST = REPLAY_DIR / "SHA256SUMS.json"
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


def test_5k_replay_regeneration_is_byte_identical(tmp_path: Path) -> None:
    hashes = []
    for index in range(3):
        output_dir = tmp_path / f"run_{index}"
        subprocess.run(
            [
                sys.executable,
                "demo/replay/generate_replay.py",
                "--scenario",
                "5k",
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            check=True,
        )
        hashes.append(_sha256(output_dir / FIVE_K_REPLAY.name))

    assert len(set(hashes)) == 1


def test_5k_replay_size_and_format_parity() -> None:
    assert FIVE_K_REPLAY.stat().st_size <= 5_000_000

    one_k = _unpack(ONE_K_REPLAY)
    five_k = _unpack(FIVE_K_REPLAY)
    assert list(five_k) == list(one_k)
    assert five_k["metadata"]["agent_count"] == 5000
    assert five_k["metadata"]["tick_count"] == 30
    assert five_k["metadata"]["grid_bounds"] == {"width": 40, "height": 40}
    assert len(five_k["agents"]) == 5000
    assert len(five_k["frames"]) == 30


def test_scenario_40x40_has_no_forbidden_entity_strings() -> None:
    text = SCENARIO_40X40.read_text(encoding="utf-8")
    assert not [forbidden for forbidden in FORBIDDEN_STRINGS if forbidden in text]


def test_existing_100_and_1k_replays_match_tracked_sha256_manifest() -> None:
    manifest = json.loads(LEGACY_SHA_MANIFEST.read_text(encoding="utf-8"))
    for filename in (
        "replay_100agents_gangnam_7pm.msgpack",
        "replay_1000agents_gangnam_7pm.msgpack",
    ):
        assert _sha256(REPLAY_DIR / filename) == manifest[filename]


def test_replay_viewer_loads_and_plays_5k_from_file_url() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(VIEWER_PATH.as_uri(), wait_until="domcontentloaded")
            page.wait_for_function("() => !document.querySelector('#scenario').disabled")
            page.select_option("#scenario", FIVE_K_REPLAY.name)
            page.locator("#file-input").set_input_files(FIVE_K_REPLAY)
            page.wait_for_function(
                "() => document.querySelector('#status').textContent.includes('5000 agents loaded')",
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
                      if (performance.now() - started > 90000) {
                        clearInterval(timer);
                        reject(new Error("5K replay did not reach final tick within 90 seconds"));
                      }
                    }, 10);
                })"""
            )
            assert float(elapsed_ms) < 90_000
        finally:
            browser.close()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unpack(path: Path) -> dict[str, object]:
    return msgpack.unpackb(path.read_bytes(), raw=False)
