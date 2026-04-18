# Social Learning Cascade

Phase 55 runs a deterministic observational learning cascade with one teacher and nineteen learners. The teacher demonstrates an efficient strategy, learners retain the behavior, and the `SocialLearner` reproduces it once motivation crosses the imitation threshold.

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python experiments\social_learning_cascade\run.py
```

Acceptance requires at least 75% propagation by tick 50.
