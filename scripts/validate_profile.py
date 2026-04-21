"""Validate offline replay archetype profile YAML files."""

from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

ETHICS_DISCLAIMER = (
    "This profile is a pedagogical, synthetic replay overlay for criminology education. "
    "It is not an operational profiling tool, a prediction, or guidance for identifying any real person."
)
FORBIDDEN_NAMES = ("Bundy", "Kemper", "Gacy", "Dahmer", "Ramirez")
RESEARCH_BY_ID = {
    "fbi-organized": "tier1_archetypes/fbi_organized_research.md",
    "fbi-disorganized": "tier1_archetypes/fbi_disorganized_research.md",
    "canter-geographic-a": "tier1_archetypes/canter_geographic_a_research.md",
    "kicrim-fraud-archetype": "tier1_archetypes/kicrim_fraud_archetype_research.md",
    "whitechapel-1888": "tier2_historical/whitechapel_1888_research.md",
    "holmes-1890s": "tier2_historical/holmes_1890s_research.md",
    "gunness-1900s": "tier2_historical/gunness_1900s_research.md",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    root = Path("demo/replay/profiles")
    schema = yaml.safe_load((root / "schema.yaml").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    failures: list[str] = []
    for path in _expand_paths(args.paths):
        if path.name == "schema.yaml":
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_NAMES:
            if forbidden in text:
                failures.append(f"{path}: forbidden Tier 3 name {forbidden}")
        payload = yaml.safe_load(text)
        if not isinstance(payload, dict):
            failures.append(f"{path}: expected mapping")
            continue
        failures.extend(_schema_failures(path, payload, validator))
        failures.extend(_policy_failures(path, payload))
        failures.extend(_citation_failures(path, payload, root))
    if failures:
        raise SystemExit("\n".join(failures))


def _expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    return sorted({path for path in paths if path.suffix in {".yaml", ".yml"}})


def _schema_failures(
    path: Path,
    payload: dict[str, Any],
    validator: Draft202012Validator,
) -> list[str]:
    failures: list[str] = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        failures.append(f"{path}: schema error at {location}: {error.message}")
    return failures


def _policy_failures(path: Path, payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    tier = payload.get("tier")
    if tier not in {1, 2}:
        failures.append(f"{path}: tier must be 1 or 2")
    if payload.get("ethical_disclaimer") != ETHICS_DISCLAIMER:
        failures.append(f"{path}: ethical_disclaimer must match profiles/ETHICS.md section 2")
    sources = payload.get("literature_sources")
    if not isinstance(sources, list) or not sources:
        failures.append(f"{path}: literature_sources must be non-empty")
    elif not any(source.get("doi") or source.get("isbn") for source in sources if isinstance(source, dict)):
        failures.append(f"{path}: at least one literature source needs DOI or ISBN")
    return failures


def _citation_failures(path: Path, payload: dict[str, Any], root: Path) -> list[str]:
    archetype_id = str(payload.get("archetype_id", ""))
    research_rel = RESEARCH_BY_ID.get(archetype_id)
    if research_rel is None:
        return [f"{path}: no research mapping for {archetype_id}"]
    research_path = root / "_research" / research_rel
    research_text = research_path.read_text(encoding="utf-8")
    appendix = research_text.split("## Citation appendix", 1)[-1]
    failures: list[str] = []
    for index, source in enumerate(payload.get("literature_sources", [])):
        if not isinstance(source, dict):
            failures.append(f"{path}: literature_sources[{index}] must be a mapping")
            continue
        identifier = _normalize_identifier(str(source.get("doi") or source.get("isbn", "")))
        if not identifier.strip():
            failures.append(f"{path}: literature_sources[{index}] missing DOI or ISBN")
            continue
        if identifier not in _normalized_appendix(appendix):
            failures.append(
                f"{path}: literature_sources[{index}] identifier {identifier} missing from {research_path}"
            )
    return failures


def _normalize_identifier(value: str) -> str:
    return re.sub(r"[-\s]", "", value)


def _normalized_appendix(text: str) -> str:
    return re.sub(r"[-\s]", "", text)


if __name__ == "__main__":
    main()
