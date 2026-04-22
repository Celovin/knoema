import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cat28_identifiers_are_in_legal_attribution() -> None:
    citation = _read("demo/replay/profiles/personality_cat28/CITATION.md")
    attribution = _read("legal/attribution.md")

    identifiers = set()
    identifiers.update(re.findall(r"10\.\d{4,9}/[^\s.)]+", citation))
    identifiers.update(re.findall(r"\b\d{3}-\d-\d{4}-\d{4}-\d\b", citation))
    identifiers.update(re.findall(r"\b\d{4}-\d{3}[\dX]\b", citation))

    assert identifiers
    missing = sorted(identifier for identifier in identifiers if identifier not in attribution)
    assert missing == []


def test_nemotron_attribution_matches_license_notice() -> None:
    license_text = _read("LICENSE-NEMOTRON.md")
    attribution = _read("legal/attribution.md")

    required_fragments = [
        "Nemotron-Personas-Korea dataset card, authors NVIDIA and Naver Cloud.",
        "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea",
        "0381f03a403df78a7998000f8b11705635b654fd",
        "cc-by-4.0",
    ]
    for fragment in required_fragments:
        assert fragment in license_text
        assert fragment in attribution
