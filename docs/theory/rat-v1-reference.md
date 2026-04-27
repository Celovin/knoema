# `luvoire.theory.rat` (v1) — Reference

`luvoire.theory.rat` is a **Tier A locked module** referenced from Scenario DSL v2 by the string ``code:luvoire.theory.rat.v1``. It encodes the routine activity theory (Cohen and Felson 1979) convergence rule as a synthetic spatio-temporal opportunity-event detector.

This module is deliberately not re-exported from the top-level :mod:`luvoire` package. It is consumed by simulators and by Scenario DSL v2 Tier A parameter references, not as part of the public application surface.

## Quick example

```python
from luvoire.theory.rat import (
    ActorState,
    TargetExposure,
    GuardianshipGap,
    opportunity_event,
)

actor = ActorState(actor_id="a", motivation=0.7, cell="synthetic-grid-r3c4", tick=7)
target = TargetExposure(target_id="t", exposure=0.7, cell="synthetic-grid-r3c4", tick=7)
guardian = GuardianshipGap(place_id="p", gap=0.7, cell="synthetic-grid-r3c4", tick=7)

event = opportunity_event(actor, target, guardian, tick=7, cell="synthetic-grid-r3c4")
if event is not None:
    print(event.convergence_score)  # 0.343
```

## Convergence rule

```
opportunity_event(actor, target, guardian, tick, cell) -> OpportunityEvent | None

Returns an OpportunityEvent iff:
    1. actor.tick == target.tick == guardian.tick == tick
    2. each input cell is the same as `cell` or adjacent to it
    3. actor.motivation * target.exposure * guardian.gap >= threshold
       (default threshold = 0.125 == 0.5^3)
```

The default threshold and the multiplicative form are **locked** by Tier A. Adjustable inputs belong in Tier B/C parameters in scenario YAML.

## Locked vs adjustable

| Element | Tier | Where it lives |
| --- | --- | --- |
| Convergence formula (multiplicative) | A | this module (locked) |
| Tick-equality requirement | A | this module (locked) |
| Cell adjacency rule | A | this module (locked) |
| `kind` literal `rat_v1_synthetic_opportunity` | A | this module (locked) |
| `threshold` value | C | scenario YAML |
| Distribution of `motivation` / `exposure` / `gap` | B | scenario YAML, with required `source` |
| Formal vs informal layer weights inside `gap` | C | scenario YAML |

## Synthetic-only guarantees

- `OpportunityEvent` is a fictional indicator of theoretical convergence, never a real-event prediction.
- The `kind` literal is locked to ``rat_v1_synthetic_opportunity`` so downstream pipelines cannot accidentally cross-stream another theory module's events.
- This module emits no LLM calls and is fully deterministic given identical inputs — replay-safe.

## Cell adjacency

`H3CellRef` accepts either:

- a 15-character h3 v4 hex index (e.g. ``"8830e1ad81fffff"``); cell adjacency is delegated to the optional ``h3-py`` runtime — installed via the v0.4 GIS extras (T2). When ``h3-py`` is absent, only equal-cell convergence is detected.
- a synthetic-grid label (e.g. ``"synthetic-grid-r3c4"``); only equal-label convergence is detected. Synthetic-grid adapters in T2 may inject custom adjacency.

## Related

- [Scenario DSL v2 Reference](../dsl/v2-reference.md)
- [`luvoire.theory.rat` v1 Design Spec](rat-v1-design-spec.md)
- [Civilian Use Policy](https://github.com/Celovin/luvoire/blob/main/POLICIES/civilian_use.md)
