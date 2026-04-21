# Trait Stability Over Time

## Research Question

How stable are trait-action relationships across early and late phases of repeated social simulation runs?

## Hypotheses

- H1. Deterministic replay will preserve trait-action rank ordering across seed batches.
- H2. High-neuroticism agents will show larger late-phase behavioral drift under stressors.

## IV/DV

- IV: tick window, trait band, stressor condition.
- DV: trait-action rank stability, late-phase drift, action entropy, emotion variance.

## Sample Size

Use at least 150 seed-window observations. Run the Playground power analysis with a paired t-test, effect size 0.40, alpha 0.05, and target power 0.80.

## Analysis Plan

Estimate rank correlations and Mann-Whitney or paired tests over drift scores. Apply multiple-testing correction across trait-action families.

## Submission Checklist

- Early and late tick windows are declared before inspection.
- Stressor events and seed ranges are frozen.
- Deviations from the planned windowing rule are logged.
