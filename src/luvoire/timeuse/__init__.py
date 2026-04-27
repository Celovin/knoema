"""Time-use prior sampler for the synthetic urban grid (numpy + stdlib only).

This subpackage models how a synthetic agent allocates a 24-hour day across
a small canonical activity vocabulary. The sampler is fully deterministic
given an integer seed and uses only numpy and the standard library.

Two complementary samplers are provided:

* :class:`EmpiricalCdfSampler` draws single activity codes from a strata-
  conditioned empirical distribution (an :class:`ActivityPrior`).
* :class:`MarkovActivitySampler` walks a 7x7 row-stochastic transition
  matrix over the same activity vocabulary.

The companion :mod:`luvoire.timeuse.kostat` registry holds *metadata only*
about KOSTAT 생활시간조사 tables; the engine never bundles or loads
microdata. Tier B parameters that declare a KOSTAT table id can be cross-
checked against the registry by future tooling.
"""

from luvoire.timeuse.kostat import (
    REGISTERED_KOSTAT_TABLES,
    KostatTable,
    lookup_kostat_table,
)
from luvoire.timeuse.markov import (
    MarkovActivitySampler,
    TransitionMatrix,
    transition_from_dict,
)
from luvoire.timeuse.priors import (
    ACTIVITY_CODES,
    ActivityCode,
    ActivityPrior,
    EmpiricalCdfSampler,
    StrataKey,
    load_priors_from_json,
)

__all__ = [
    "ACTIVITY_CODES",
    "REGISTERED_KOSTAT_TABLES",
    "ActivityCode",
    "ActivityPrior",
    "EmpiricalCdfSampler",
    "KostatTable",
    "MarkovActivitySampler",
    "StrataKey",
    "TransitionMatrix",
    "load_priors_from_json",
    "lookup_kostat_table",
    "transition_from_dict",
]
