"""Mesa 3 adapter for Luvoire simulations.

The package intentionally imports Mesa only when this optional adapter is
imported, so `import luvoire` remains independent of the `luvoire[mesa]` extra.
"""

from luvoire.adapters.mesa.agent import LuvoireMesaAgent
from luvoire.adapters.mesa.model import LuvoireMesaModel, to_mesa_model

__all__ = [
    "LuvoireMesaAgent",
    "LuvoireMesaModel",
    "to_mesa_model",
]
