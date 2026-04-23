"""Mesa Agent wrapper for a Luvoire Persona."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, cast

from luvoire.persona import Persona

if TYPE_CHECKING:
    from luvoire.adapters.mesa.model import LuvoireMesaModel

mesa = importlib.import_module("mesa")


class LuvoireMesaAgent(mesa.Agent):  # type: ignore[misc,name-defined]
    """Mesa-visible wrapper around a Luvoire `Persona`."""

    def __init__(self, model: LuvoireMesaModel, luv_agent: Persona) -> None:
        super().__init__(model)
        self.luv = luv_agent

    def step(self) -> None:
        model = cast("LuvoireMesaModel", self.model)
        observation = model.observe(self.luv)
        action = model.act(self.luv, observation)
        model.apply(self.luv, action)
