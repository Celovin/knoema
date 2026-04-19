"""Cognitive extension modules."""

from knoema.cognition.monologue import Monologue, MonologueGenerator
from knoema.cognition.social_learning import (
    LearnedSkill,
    ObservedBehavior,
    SocialLearner,
)

__all__ = [
    "LearnedSkill",
    "Monologue",
    "MonologueGenerator",
    "ObservedBehavior",
    "SocialLearner",
]
