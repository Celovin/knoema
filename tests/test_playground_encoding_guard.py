"""Regression guard for Korean string encoding in playground sources.

A prior Codex pass wrote app.py with the wrong codec, corrupting Korean
labels (e.g. 'OSF 사전등록' became 'OSF ?ъ쟾?깅줉' or strings with
U+FFFD). The user only saw this when the live UI rendered. This guard
scans the playground source files for U+FFFD so a future regression
fails CI instead of reaching the HF Space. Codex can extend this guard
with finer mojibake heuristics later.
"""

from __future__ import annotations

import re
from pathlib import Path

PLAYGROUND_DIR = Path(__file__).resolve().parent.parent / "playground"
SCANNED_FILES = ("app.py", "simulation.py", "voice.py", "hexaco_questionnaire.py", "quest_generation.py")
REPLACEMENT_CHAR = "\ufffd"
SUSPICIOUS_QUESTION_KOREAN_RE = re.compile(r"\?[^\s\?\"'`<>{}\[\]()]{0,6}[가-힣ㄱ-ㅎㅏ-ㅣ]+")
MOJIBAKE_WHITELIST_FRAGMENTS = (
    'raw_choice in {"日本語", "日本语"}',
    'raw_choice in {"中文", "简体中文", "繁體中文"}',
    "BibTeX",
    "bibtex",
    "citation",
)


def _is_whitelisted_mojibake_line(raw: str) -> bool:
    return any(fragment in raw for fragment in MOJIBAKE_WHITELIST_FRAGMENTS)


def _has_suspicious_question_korean_sequences(raw: str) -> bool:
    if _is_whitelisted_mojibake_line(raw):
        return False
    return len(SUSPICIOUS_QUESTION_KOREAN_RE.findall(raw)) >= 2


def test_no_replacement_char_in_playground_sources() -> None:
    failures: list[str] = []
    for filename in SCANNED_FILES:
        path = PLAYGROUND_DIR / filename
        if not path.exists():
            continue
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if REPLACEMENT_CHAR in raw:
                failures.append(f"{filename}:{lineno}: contains U+FFFD: {raw.strip()[:120]!r}")
            if _has_suspicious_question_korean_sequences(raw):
                failures.append(f"{filename}:{lineno}: suspicious '?'+Korean mojibake pattern: {raw.strip()[:120]!r}")
    assert not failures, "U+FFFD replacement chars detected in playground sources:\n" + "\n".join(failures)


def test_question_mark_korean_mojibake_heuristic_flags_multiple_sequences() -> None:
    assert _has_suspicious_question_korean_sequences("OSF ?ъ쟾?깅줉 안내")
    assert _has_suspicious_question_korean_sequences("텍스트 ?좎냼?붿껌 ?댁슜")


def test_question_mark_korean_mojibake_heuristic_whitelists_expected_lines() -> None:
    assert not _has_suspicious_question_korean_sequences(
        'if raw_choice in {"日本語", "日本语"} or lowered_choice in {"ja", "japanese"}:'
    )
    assert not _has_suspicious_question_korean_sequences(
        '@article{demo, title={BibTeX citation for 中文 / 繁體中文 localization}}'
    )
