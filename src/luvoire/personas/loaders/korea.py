"""Korea Nemotron-Personas loader.

The legacy Korea-only path remains available at
``luvoire.persona.nemotron_loader.NemotronPersonaSource``.
"""

from __future__ import annotations

from collections.abc import Iterator

from luvoire.personas.loaders.korea_mapping import CONFIG
from luvoire.personas.loaders.nemotron_base import iter_country_personas
from luvoire.personas.lpi import LPIPersona


def iter_personas() -> Iterator[LPIPersona]:
    return iter_country_personas(CONFIG)


__all__ = ["CONFIG", "iter_personas"]
