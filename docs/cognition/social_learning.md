# Social Learning

Phase 55 adds opt-in observational imitation. Personas keep the previous behavior by default; set `social_learning=True` to let an agent observe successful behaviors and reproduce them later.

The implementation follows a compact Bandura-style loop:

- Attention: ignore self-observation and uninformative `wait` actions.
- Retention: keep a bounded observation buffer per learner.
- Reproduction: convert the highest-motivation learned skill into a normal `Action`.
- Motivation: increase imitation likelihood when observed outcomes are successful.

```python
from knoema import Persona

learner = Persona(..., social_learning=True)
```

The cascade experiment is stored in `experiments/social_learning_cascade`. The committed result reaches a 1.000 propagation rate by tick 50 against the 0.750 acceptance target.
