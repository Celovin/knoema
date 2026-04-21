# Agent Imitation and Influence

## Research Question

Do high-status or high-centrality agents shape the action choices of other agents through imitation?

## Hypotheses

- H1. High-status or high-centrality agents will be imitated more often after visible actions.
- H2. Social-learning enabled runs will converge faster than social-learning disabled controls.

## IV/DV

- IV: social learning toggle, initial centrality band, visible action event.
- DV: imitation event rate, convergence speed, action diversity, centrality change.

## Sample Size

Use at least 144 matched seed observations. Run the Playground power analysis with a paired t-test, effect size 0.45, alpha 0.05, and target power 0.80.

## Analysis Plan

Use paired-seed comparisons and event-count models with robust confidence intervals. Report source-agent centrality bands.

## Submission Checklist

- Imitation detection rules are declared before analysis.
- Centrality priors and visible actions are frozen.
- Seed-matched controls are included.
