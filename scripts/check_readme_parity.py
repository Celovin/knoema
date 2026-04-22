from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "README.md"
LOCALES = (
    "README.de.md",
    "README.es.md",
    "README.fr.md",
    "README.ja.md",
    "README.ko.md",
    "README.zh-CN.md",
    "README.zh-TW.md",
)
RAW_ENGLISH_DRIFT = (
    "Knoema Bench is the seven-axis public leaderboard",
    "1K city-scale benchmark, offline msgpack replay viewer, and pedagogical archetype overlays",
    "Unity SDK (preview) with FastAPI tick/memory/action contract and UPM package layout",
    "Opt-in OpenAI TTS voice playback for Playground timeline",
)


@dataclass(frozen=True, slots=True)
class Feature:
    key: str
    label: str
    patterns: tuple[str, ...]


FEATURES = (
    Feature(
        key="cat28",
        label="CAT-28 tier 5 personality",
        patterns=(r"CAT-28", r"(tier 5|티어 5|Stufe 5|nivel 5|niveau 5|ティア5|五级|五級)"),
    ),
    Feature(
        key="unity_sdk",
        label="Unity SDK preview",
        patterns=(r"Unity SDK", r"(preview|Vorschau|vista previa|aperçu|プレビュー|미리보기|预览|預覽)"),
    ),
    Feature(
        key="bench",
        label="Knoema Bench leaderboard",
        patterns=(r"Knoema Bench", r"celovin\.github\.io/knoema/bench|bench/submissions/TEMPLATE\.yaml"),
    ),
    Feature(
        key="city_1k",
        label="city-scale 1k benchmark",
        patterns=(r"(1K|1천|1000)", r"(city-scale|City-scale|urbano|urbain|都市|도시|城市)"),
    ),
    Feature(
        key="openai_tts",
        label="OpenAI TTS voice playback",
        patterns=(r"OpenAI TTS", r"(voice playback|Sprachwiedergabe|reproducción de voz|lecture vocale|音声再生|음성 재생|语音播放|語音播放)"),
    ),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE | re.IGNORECASE))


def _has_feature(text: str, feature: Feature) -> bool:
    return all(re.search(pattern, text, flags=re.IGNORECASE) for pattern in feature.patterns)


def _markdown_stats(text: str) -> tuple[int, int]:
    heading_count = _count(r"^##\s+", text)
    bullet_count = _count(r"^-\s+", text)
    return heading_count, bullet_count


def check_readme_parity() -> int:
    canonical_text = _read(CANONICAL)
    canonical_headings, canonical_bullets = _markdown_stats(canonical_text)
    failures: list[str] = []
    rows: list[tuple[str, int, int, str]] = []

    for locale in LOCALES:
        path = ROOT / locale
        text = _read(path)
        heading_count, bullet_count = _markdown_stats(text)
        missing = [feature.label for feature in FEATURES if not _has_feature(text, feature)]
        raw_english = [phrase for phrase in RAW_ENGLISH_DRIFT if phrase in text]
        if raw_english:
            missing.extend(f"untranslated English drift: {phrase}" for phrase in raw_english)
        if missing:
            failures.append(f"{locale}: " + "; ".join(missing))
        rows.append((locale, heading_count, bullet_count, ", ".join(missing) if missing else "OK"))

    print("| README | ## headings | bullets | missing recent feature parity |")
    print("| --- | ---: | ---: | --- |")
    print(f"| README.md | {canonical_headings} | {canonical_bullets} | canonical |")
    for locale, heading_count, bullet_count, missing in rows:
        print(f"| {locale} | {heading_count} | {bullet_count} | {missing} |")

    if failures:
        print("\nREADME parity drift detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    raise SystemExit(check_readme_parity())


if __name__ == "__main__":
    main()
