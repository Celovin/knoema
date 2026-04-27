"""Multi-layer relationship networks for the Luvoire engine.

This subpackage layers a 5-channel social graph (family / coworker /
classmate / neighbor / online) on top of the existing single-layer
:class:`luvoire.relationship.RelationshipGraph` without breaking any
of its callers. The flatten helper collapses the multi-layer graph
back into the legacy structure so existing code continues to work.

Both `py3plex` and `NDlib` are treated as optional runtime
dependencies. The default code paths in this subpackage rely only on
the Python standard library and numpy, which keeps the deterministic
fallbacks aligned with the rest of Luvoire's reproducibility surface.
"""

from luvoire.netlayers.contagion import AffectiveContagion
from luvoire.netlayers.diffusion import DeGrootPropagator
from luvoire.netlayers.multilayer import (
    LAYER_NAMES,
    MultilayerEdge,
    MultilayerRelationshipGraph,
    RelationshipLayer,
)

__all__ = [
    "LAYER_NAMES",
    "AffectiveContagion",
    "DeGrootPropagator",
    "MultilayerEdge",
    "MultilayerRelationshipGraph",
    "RelationshipLayer",
]
