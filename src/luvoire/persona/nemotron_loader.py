"""Nemotron-Personas-Korea loader for deterministic synthetic persona seeding."""

from __future__ import annotations

import hashlib
import heapq
import importlib
import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

DEFAULT_REPO_ID = "nvidia/Nemotron-Personas-Korea"
DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "nemotron_sample_512.jsonl"
GANGNAM_ALIASES = {"gangnam", "gangnamgu", "gangnam-gu", "강남", "강남구"}
EXPECTED_AGENT_ATTRIBUTE_KEYS = (
    "persona_id",
    "age",
    "age_band",
    "gender",
    "occupation",
    "region",
    "income_band",
    "education",
    "household",
)

PersonaRecord = dict[str, Any]


@dataclass(slots=True)
class NemotronPersonaSource:
    """Stream and deterministically sample synthetic Korean personas."""

    # deprecated: migrate new cross-country callers to
    # luvoire.personas.loaders.korea.iter_personas().
    repo_id: str = DEFAULT_REPO_ID
    cache_dir: str | Path | None = None
    hf_token: str | None = None
    fixture_path: str | Path | None = None

    def load(self, streaming: bool = True) -> Iterable[Mapping[str, Any]]:
        """Return a streaming dataset handle or an offline JSONL fixture iterator."""

        fixture = self._fixture_path()
        if fixture is not None:
            return _iter_jsonl(fixture)
        datasets = importlib.import_module("datasets")
        loaded = datasets.load_dataset(
            self.repo_id,
            split="train",
            streaming=streaming,
            cache_dir=str(self.cache_dir) if self.cache_dir is not None else None,
            token=self.hf_token or None,
        )
        return cast(Iterable[Mapping[str, Any]], loaded)

    def sample(
        self,
        n: int,
        seed: int,
        filters: Mapping[str, str] | None = None,
    ) -> list[PersonaRecord]:
        """Return exactly ``n`` deterministic personas for the given seed."""

        if n < 1:
            raise ValueError("n must be positive")
        dataset = self.load(streaming=True)
        filtered = self._apply_filters(dataset, filters)
        heap: list[tuple[int, int, PersonaRecord]] = []
        for index, row in enumerate(filtered):
            record = dict(row)
            score = _score(seed, _persona_id(record), index)
            entry = (-score, -index, record)
            if len(heap) < n:
                heapq.heappush(heap, entry)
            elif entry > heap[0]:
                heapq.heapreplace(heap, entry)
        selected = [
            record
            for _negative_score, _negative_index, record in sorted(
                heap,
                key=lambda item: (-item[0], -item[1]),
            )
        ]
        if not selected:
            raise ValueError("filters returned no Nemotron personas")
        if len(selected) >= n:
            return selected[:n]
        repeated: list[PersonaRecord] = []
        while len(repeated) < n:
            for record in selected:
                repeated.append(dict(record))
                if len(repeated) == n:
                    break
        return repeated

    def to_agent_attributes(self, persona: Mapping[str, Any]) -> dict[str, Any]:
        """Map a Nemotron row into Luvoire replay demographics."""

        age = _coerce_age(persona.get("age"))
        region = _region(persona)
        return {
            "persona_id": _persona_id(persona),
            "age": age,
            "age_band": _age_band(age),
            "gender": _string_or_default(persona.get("sex")),
            "occupation": _string_or_default(persona.get("occupation")),
            "region": region,
            "income_band": _string_or_default(persona.get("income"), default="unknown"),
            "education": _string_or_default(persona.get("education_level")),
            "household": _string_or_default(
                persona.get("family_type") or persona.get("housing_type")
            ),
        }

    def _fixture_path(self) -> Path | None:
        if self.fixture_path is not None:
            return Path(self.fixture_path)
        if self.repo_id.startswith("file:"):
            return Path(self.repo_id.removeprefix("file:"))
        if self.repo_id in {"fixture", "local-fixture"}:
            return DEFAULT_FIXTURE_PATH
        return None

    def _apply_filters(
        self,
        dataset: Iterable[Mapping[str, Any]],
        filters: Mapping[str, str] | None,
    ) -> Iterable[Mapping[str, Any]]:
        if not filters:
            return dataset

        def predicate(row: Mapping[str, Any]) -> bool:
            return _matches_filters(row, filters)

        if hasattr(dataset, "filter"):
            return cast(Iterable[Mapping[str, Any]], dataset.filter(predicate))
        return (row for row in dataset if predicate(row))


def _iter_jsonl(path: Path) -> Iterator[Mapping[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    yield payload


def _matches_filters(row: Mapping[str, Any], filters: Mapping[str, str]) -> bool:
    region = _normalized_region(_region(row))
    exact_region = filters.get("region")
    if exact_region is not None and region != _normalized_region(exact_region):
        return False
    contains = filters.get("region_contains")
    if contains is not None:
        needles = _region_needles(contains)
        if not any(needle in region for needle in needles):
            return False
    return True


def _region(row: Mapping[str, Any]) -> str:
    province = _string_or_default(row.get("province"))
    district = _string_or_default(row.get("district"))
    if province == "unknown":
        return district
    if district == "unknown":
        return province
    return district if district.startswith(province) else f"{province}-{district}"


def _region_needles(value: str) -> tuple[str, ...]:
    normalized = _normalized_region(value)
    needles = {normalized}
    if normalized in GANGNAM_ALIASES:
        needles.update({"강남", "강남구", "gangnam"})
    return tuple(sorted(needles))


def _normalized_region(value: str) -> str:
    return (
        value.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace("gu", "구")
    )


def _persona_id(row: Mapping[str, Any]) -> str:
    identifier = row.get("uuid") or row.get("persona_id")
    if isinstance(identifier, str) and identifier.strip():
        return identifier.strip()
    encoded = json.dumps(dict(row), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def _score(seed: int, persona_id: str, index: int) -> int:
    digest = hashlib.sha256(f"{seed}:{persona_id}:{index}".encode()).hexdigest()
    return int(digest[:16], 16)


def _coerce_age(value: Any) -> int:
    try:
        age = int(value)
    except (TypeError, ValueError):
        return 35
    return min(100, max(1, age))


def _age_band(age: int) -> str:
    decade = max(10, min(90, (age // 10) * 10))
    return f"{decade}s"


def _string_or_default(value: Any, *, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


__all__ = [
    "DEFAULT_FIXTURE_PATH",
    "DEFAULT_REPO_ID",
    "EXPECTED_AGENT_ATTRIBUTE_KEYS",
    "NemotronPersonaSource",
]
