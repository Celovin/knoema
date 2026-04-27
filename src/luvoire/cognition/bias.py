"""Cognitive-bias prefix templates for the cognition middleware.

A small registry of bias-injection prefixes that callers can attach to the
front of an LLM prompt. The library does not invoke an LLM itself; it returns
a string prefix selected deterministically from a seed plus the requested
bias set.

Bias names follow the canonical experimental psychology terminology used by
Kahneman/Tversky and the Knipper-220 / Malberg-30 evaluation sets so future
acceptance tests can match by name.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

BiasName = Literal[
    "availability",
    "confirmation",
    "anchoring",
    "framing",
    "hyperbolic_discounting",
    "loss_aversion",
    "status_quo",
    "representativeness",
]

CANONICAL_BIASES: tuple[BiasName, ...] = (
    "availability",
    "confirmation",
    "anchoring",
    "framing",
    "hyperbolic_discounting",
    "loss_aversion",
    "status_quo",
    "representativeness",
)

_BIAS_TEMPLATES: dict[BiasName, str] = {
    "availability": (
        "You weight recent and vivid memories more heavily than older ones."
    ),
    "confirmation": (
        "You give greater weight to evidence that supports your existing belief."
    ),
    "anchoring": (
        "Your estimates stay close to the first concrete number you encounter."
    ),
    "framing": (
        "Your decision shifts when the same option is described as gain vs loss."
    ),
    "hyperbolic_discounting": (
        "You strongly prefer immediate small rewards over larger delayed rewards."
    ),
    "loss_aversion": (
        "Avoiding a loss matters about twice as much as obtaining an equivalent gain."
    ),
    "status_quo": (
        "You prefer to keep the current arrangement unless a clear improvement appears."
    ),
    "representativeness": (
        "You judge probability by similarity to a stereotype rather than base rates."
    ),
}


@dataclass(frozen=True, slots=True)
class BiasPrefix:
    """A composed bias-prefix payload."""

    biases: tuple[BiasName, ...]
    prefix_text: str
    fingerprint: str


def render_bias_prefix(
    biases: Sequence[BiasName],
    *,
    seed: int,
) -> BiasPrefix:
    """Compose a deterministic bias-prefix string for the requested biases.

    The biases are rendered in canonical order (the order in
    :data:`CANONICAL_BIASES`), regardless of the input order, so two callers
    requesting the same set always get the same prefix string. ``seed`` is
    threaded into the fingerprint so callers can audit which prefix was
    actually presented to the LLM in a given run.

    Raises:
        ValueError: When an unknown bias name is requested or the input is
            empty.
    """

    if not biases:
        raise ValueError("at least one bias name is required")
    requested = set(biases)
    unknown = requested - set(CANONICAL_BIASES)
    if unknown:
        raise ValueError(f"unknown bias names: {sorted(unknown)}")
    ordered = tuple(name for name in CANONICAL_BIASES if name in requested)
    sentences = [_BIAS_TEMPLATES[name] for name in ordered]
    prefix_text = " ".join(sentences)
    fingerprint = hashlib.sha256(
        f"{seed}|{'+'.join(ordered)}|{prefix_text}".encode()
    ).hexdigest()
    return BiasPrefix(
        biases=ordered,
        prefix_text=prefix_text,
        fingerprint=fingerprint,
    )


__all__ = [
    "CANONICAL_BIASES",
    "BiasName",
    "BiasPrefix",
    "render_bias_prefix",
]
