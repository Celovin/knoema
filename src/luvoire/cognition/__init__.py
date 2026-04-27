"""Cognitive extension modules.

Adds three middleware layers on top of the original Monologue + SocialLearner
surface: a dual-process Sys-1/Sys-2 router, an attention-budget allocator,
and a bias-prefix template registry. The middleware layers are pure
deterministic helpers — they do not call an LLM by themselves; callers
compose them around their own LLM gateway invocations.
"""

from luvoire.cognition.attention import (
    AttentionDecision,
    AttentionItem,
    allocate_attention,
)
from luvoire.cognition.bias import (
    CANONICAL_BIASES,
    BiasName,
    BiasPrefix,
    render_bias_prefix,
)
from luvoire.cognition.dual_process import (
    RouteLabel,
    RoutingDecision,
    TriggerSignal,
    route_decision,
)
from luvoire.cognition.monologue import Monologue, MonologueGenerator
from luvoire.cognition.social_learning import (
    LearnedSkill,
    ObservedBehavior,
    SocialLearner,
)

__all__ = [
    "CANONICAL_BIASES",
    "AttentionDecision",
    "AttentionItem",
    "BiasName",
    "BiasPrefix",
    "LearnedSkill",
    "Monologue",
    "MonologueGenerator",
    "ObservedBehavior",
    "RouteLabel",
    "RoutingDecision",
    "SocialLearner",
    "TriggerSignal",
    "allocate_attention",
    "render_bias_prefix",
    "route_decision",
]
