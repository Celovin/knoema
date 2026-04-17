"""PAD emotion state model."""

from __future__ import annotations

from dataclasses import dataclass

from knoema.types import Emotion


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass(slots=True)
class EmotionStimulus:
    valence_delta: float = 0.0
    arousal_delta: float = 0.0
    dominance_delta: float = 0.0


class EmotionState:
    """Mutable PAD state with decay and stimulus updates."""

    def __init__(self, initial: Emotion | None = None) -> None:
        self.current = initial or Emotion(valence=0.0, arousal=0.2, dominance=0.5)

    def apply(self, stimulus: EmotionStimulus) -> Emotion:
        self.current = Emotion(
            valence=_clamp(
                self.current.valence + stimulus.valence_delta,
                minimum=-1.0,
                maximum=1.0,
            ),
            arousal=_clamp(
                self.current.arousal + stimulus.arousal_delta,
                minimum=0.0,
                maximum=1.0,
            ),
            dominance=_clamp(
                self.current.dominance + stimulus.dominance_delta,
                minimum=0.0,
                maximum=1.0,
            ),
        )
        return self.current

    def decay(self, rate: float = 0.1) -> Emotion:
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"rate must be between 0.0 and 1.0, got {rate!r}")
        self.current = Emotion(
            valence=self.current.valence * (1.0 - rate),
            arousal=self.current.arousal * (1.0 - rate),
            dominance=0.5 + ((self.current.dominance - 0.5) * (1.0 - rate)),
        )
        return self.current

    def update_after_outcome(self, outcome: str) -> Emotion:
        mapping = {
            "positive": EmotionStimulus(valence_delta=0.18, arousal_delta=0.08, dominance_delta=0.05),
            "neutral": EmotionStimulus(arousal_delta=-0.02),
            "negative": EmotionStimulus(
                valence_delta=-0.22,
                arousal_delta=0.14,
                dominance_delta=-0.08,
            ),
        }
        try:
            stimulus = mapping[outcome]
        except KeyError as exc:
            raise ValueError(f"unknown outcome: {outcome!r}") from exc
        return self.apply(stimulus)


__all__ = ["EmotionState", "EmotionStimulus"]
