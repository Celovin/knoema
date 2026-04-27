"""Theory modules referenced as Tier A code constants by Scenario DSL v2.

These modules encode locked theoretical definitions. They are intentionally
not re-exported from :mod:`luvoire` and should be referenced from scenario
YAML only via Tier A ``ref`` strings of the form ``code:luvoire.theory.X.vN``.
"""

from luvoire.theory import rat

__all__ = ["rat"]
