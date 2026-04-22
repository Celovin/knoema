# Human Study Protocol

Phase 58 adds a lightweight protocol for judging simulation realism with blinded raters. The protocol is designed for small internal pilots, partner walkthroughs, and academic pre-registration drafts. It is not a substitute for institutional review when a study involves real participants, sensitive populations, or non-public data.

## Study Frame

Goal: compare two anonymized simulation traces for persona fidelity, memory use, relationship coherence, and overall believability.

Recommended sample: 5 to 15 raters for a protocol pilot, then 30 or more raters for a publishable study.

Artifacts:

- `evaluation/templates/realism_survey.yaml`
- `evaluation/templates/preference_pairwise.yaml`
- `evaluation/templates/turing_style.yaml`
- `evaluation/web/`
- `evaluation/samples/pilot_ratings.json`

## Workflow

1. Generate paired traces from fixed seeds.
2. Strip agent IDs that reveal framework identity.
3. Assign randomized left and right order per pair.
4. Show raters one pair at a time.
5. Collect a discrete label and an optional short rationale.
6. Export ratings by item and rater.
7. Run `compute_inter_rater_reliability`.
8. Report pairwise Cohen kappa and Fleiss kappa with the sample size.

## Checklist

- [ ] The study question is written in one sentence.
- [ ] The trace source and version are recorded.
- [ ] The scenario seed is recorded.
- [ ] The framework labels are blinded.
- [ ] Left and right ordering is randomized.
- [ ] Raters see the same instruction text.
- [ ] Raters can choose tie or unsure where appropriate.
- [ ] Free-text rationale is optional.
- [ ] No real personal data appears in traces.
- [ ] No production secrets appear in traces.
- [ ] Public-safety examples remain fictional and synthetic.
- [ ] The sample size is justified.
- [ ] Inclusion and exclusion criteria are documented.
- [ ] Compensation policy is documented if applicable.
- [ ] Consent language is reviewed.
- [ ] Data retention duration is documented.
- [ ] Export format is JSON or CSV.
- [ ] Reliability metrics are computed before preference claims.
- [ ] Low-agreement items are inspected before publication.
- [ ] The final report distinguishes pilot evidence from measured user outcomes.

## Python API

```python
from luvoire.evaluation import compute_inter_rater_reliability

ratings = {
    "pair_001": {"rater_a": "left", "rater_b": "left", "rater_c": "right"},
    "pair_002": {"rater_a": "right", "rater_b": "right", "rater_c": "right"},
}

report = compute_inter_rater_reliability(ratings)
print(report.fleiss_kappa)
```

The pilot gate in the helper marks a session as ready for a larger run when both average pairwise Cohen kappa and Fleiss kappa are at least 0.4.
