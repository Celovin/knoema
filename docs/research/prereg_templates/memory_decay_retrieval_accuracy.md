# Memory Decay and Retrieval Accuracy

## Research Question

How does simulated delay affect retrieval accuracy for high- and low-salience events in persistent agent memory?

## Hypotheses

- H1. Longer simulated delay will reduce retrieval accuracy for low-salience events.
- H2. Reflection and long-term retrieval will preserve decision-relevant events better than neutral observations.

## IV/DV

- IV: delay window, event salience, retrieval layer.
- DV: retrieval accuracy, hallucinated recall rate, decision relevance.

## Sample Size

Use at least 200 probe-level observations. Run the Playground power analysis with a paired t-test, effect size 0.35, alpha 0.05, and target power 0.85.

## Analysis Plan

Use paired delay-window tests and report retrieval curves with confidence intervals. Separate low- and high-salience probes.

## Submission Checklist

- Retrieval probes and event salience labels are frozen.
- Delay windows are declared before running.
- Memory export and reproducibility certificate are attached.
