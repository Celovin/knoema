# Scoring Benchmarks

Phase 46 computes two heuristic quality metrics from committed JSONL artifacts:

- Persona Consistency Score (PCS)
- Relationship Coherence Score (RCS)

Run:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python benchmarks\scoring\runner.py
```

Outputs:

- `results/metrics.json`
- `results/metrics.svg`

Current committed results:

- 50-agent village PCS average: `0.948`
- 500-agent metropolis RCS average: `0.760`

The acceptance gates for Phase 46 are PCS `>= 0.75` and RCS `>= 0.70`.
