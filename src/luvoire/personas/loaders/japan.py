"""Japan Nemotron-Personas loader."""

from __future__ import annotations

from collections.abc import Iterator

from luvoire.personas.loaders.japan_mapping import CONFIG
from luvoire.personas.loaders.nemotron_base import iter_country_personas
from luvoire.personas.lpi import LPIPersona


def iter_personas() -> Iterator[LPIPersona]:
    return iter_country_personas(CONFIG)


__all__ = ["CONFIG", "iter_personas"]
