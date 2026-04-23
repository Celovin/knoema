"""Loader registry for Nemotron-Personas country datasets."""

from __future__ import annotations

import hashlib
import heapq
import importlib
from collections.abc import Iterator
from itertools import islice
from typing import cast

from luvoire.personas.loaders.nemotron_base import CountryConfig
from luvoire.personas.lpi import COUNTRY_ISO, LPIPersona

COUNTRIES: tuple[COUNTRY_ISO, ...] = ("USA", "JPN", "IND", "BRA", "SGP", "FRA", "KOR")
_MODULE_BY_ISO: dict[str, str] = {
    "USA": "luvoire.personas.loaders.usa",
    "JPN": "luvoire.personas.loaders.japan",
    "IND": "luvoire.personas.loaders.india",
    "BRA": "luvoire.personas.loaders.brazil",
    "SGP": "luvoire.personas.loaders.singapore",
    "FRA": "luvoire.personas.loaders.france",
    "KOR": "luvoire.personas.loaders.korea",
}


def list_countries() -> tuple[COUNTRY_ISO, ...]:
    return COUNTRIES


def list_country_metadata() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for iso in COUNTRIES:
        config = _config_for(iso)
        rows.append(
            {
                "iso": config.iso,
                "population_source": config.population_source,
                "record_count": config.record_count,
                "license": config.license,
                "grounding_version": config.grounding_version,
                "hf_id": config.hf_id,
            }
        )
    return tuple(rows)


def load_country(
    iso: str,
    *,
    limit: int | None = None,
    seed: int | None = None,
) -> Iterator[LPIPersona]:
    normalized = iso.upper()
    if normalized not in _MODULE_BY_ISO:
        raise ValueError(f"unsupported country ISO: {iso}")
    module = importlib.import_module(_MODULE_BY_ISO[normalized])
    personas = module.iter_personas()
    if limit is None:
        return iter(personas)
    if limit < 1:
        raise ValueError("limit must be positive")
    if seed is None:
        return islice(personas, limit)
    return iter(_stable_sample(personas, limit=limit, seed=seed))


def _config_for(iso: COUNTRY_ISO) -> CountryConfig:
    module = importlib.import_module(_MODULE_BY_ISO[iso])
    return cast(CountryConfig, module.CONFIG)


def _stable_sample(
    personas: Iterator[LPIPersona],
    *,
    limit: int,
    seed: int,
) -> list[LPIPersona]:
    heap: list[tuple[int, int, LPIPersona]] = []
    for index, persona in enumerate(personas):
        score = _score(seed, persona.persona_id, index)
        entry = (-score, -index, persona)
        if len(heap) < limit:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)
    selected = [
        persona
        for _negative_score, _negative_index, persona in sorted(
            heap,
            key=lambda item: (-item[0], -item[1]),
        )
    ]
    return selected[:limit]


def _score(seed: int, persona_id: str, index: int) -> int:
    digest = hashlib.sha256(f"{seed}:{persona_id}:{index}".encode()).hexdigest()
    return int(digest[:16], 16)


__all__ = [
    "COUNTRIES",
    "list_countries",
    "list_country_metadata",
    "load_country",
]
