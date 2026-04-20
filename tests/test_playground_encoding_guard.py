"""Regression guard for Korean string encoding in playground sources.

A prior Codex pass wrote app.py with the wrong codec, corrupting Korean
labels (e.g. 'OSF 사전등록' became 'OSF ?ъ쟾?깅줉' or strings with
U+FFFD). The user only saw this when the live UI rendered. This guard
scans the playground source files for U+FFFD so a future regression
fails CI instead of reaching the HF Space. Codex can extend this guard
with finer mojibake heuristics later.
"""

from __future__ import annotations

from pathlib import Path

PLAYGROUND_DIR = Path(__file__).resolve().parent.parent / "playground"
SCANNED_FILES = ("app.py", "simulation.py", "voice.py", "hexaco_questionnaire.py", "quest_generation.py")
REPLACEMENT_CHAR = "\ufffd"


def test_no_replacement_char_in_playground_sources() -> None:
    failures: list[str] = []
    for filename in SCANNED_FILES:
        path = PLAYGROUND_DIR / filename
        if not path.exists():
            continue
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if REPLACEMENT_CHAR in raw:
                failures.append(f"{filename}:{lineno}: contains U+FFFD: {raw.strip()[:120]!r}")
    assert not failures, "U+FFFD replacement chars detected in playground sources:\n" + "\n".join(failures)
