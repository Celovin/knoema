from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_attribution_build_is_repeatable_and_checkable() -> None:
    command = [sys.executable, "scripts/build_attributions.py"]
    subprocess.run(command, cwd=ROOT, check=True)
    first = (ROOT / "ATTRIBUTIONS.md").read_bytes()
    subprocess.run(command, cwd=ROOT, check=True)
    second = (ROOT / "ATTRIBUTIONS.md").read_bytes()

    assert first == second
    subprocess.run([*command, "--check"], cwd=ROOT, check=True)


def test_attributions_include_required_sources() -> None:
    text = (ROOT / "ATTRIBUTIONS.md").read_text(encoding="utf-8")

    required = [
        "NVIDIA",
        "CC-BY-4.0",
        "KOSIS",
        "Azuma",
        "Condry",
        "Galbraith",
        "Saito",
        "Black",
        "Matsui",
        "Whitechapel",
        "Holmes",
        "Gunness",
    ]
    for fragment in required:
        assert fragment in text

