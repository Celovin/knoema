# SSCI submission draft (international computational social science journals)

**Working title**: Auditable Routine Activity Theory in a Synthetic Korean-Style Urban Grid: Variable 3-tier Exposure and Deterministic Replay

**Authors**: Choi Jihwan (Celovin) · [Co-authors TBD pending advisor consent]
**Target venues**: *Journal of Quantitative Criminology*, *Computational and Mathematical Organization Theory*, or *PLOS ONE* computational social science track. Possible arXiv preprint first.
**Submission target**: 2027-12 (end of didimdol R&D period)

## Abstract (250 words)

Routine activity theory (RAT) describes crime opportunity as the spatio-temporal convergence of a motivated offender, a suitable target, and the absence of capable guardianship. Translating RAT into a transparent agent-based model usually means burying the convergence rule inside opaque code and exposing only numeric knobs, which makes it difficult for reviewers to tell which claims are theoretical, which are empirical, and which are exploratory. We present a deterministic Python ABM in which the RAT convergence rule is locked as a code-level constant referenced from scenario YAML by a typed string (Tier A), empirical priors must declare their data source (Tier B), and exploration knobs must declare a numeric range and a default (Tier C). Scenarios are loaded by a versioned DSL whose ethics block defaults to ``no_real_geometry: true``: any non-synthetic coordinate-system label is rejected at validation time. Every run is identified by a content hash over scenario YAML, code tree, and seed; replay equality is verified by a five-baseline SHA-256 invariant table that the continuous-integration job re-checks on every push. Across a 4096-sample Saltelli design (20 480 model evaluations), Sobol indices for the three RAT components are nearly symmetric — first-order ≈ 0.23 and total-order ≈ 0.54 each — and the gap between total and first-order indices confirms approximately thirty percent of the output variance is interaction effects. The framework is fictional, synthetic, and non-identifying by construction; the engine refuses defense, predictive-policing, PSYOP, non-consenting twinning, and minors-in-synthetic-pipelines applications by published policy.

## 1. Introduction

(See `methodology_section.md` for the canonical methods text shared by both KCI and SSCI drafts.)

Crime ABMs have grown substantially since Brantingham and colleagues' early environmental criminology models. The arrival of LLM-driven generative agents (Park et al. 2023, CrimeMind 2025) opened a new failure mode: theoretical assumptions, empirical priors, and exploratory knobs now sit on the same flat YAML or prompt surface, leaving reviewers no way to distinguish them. This paper proposes a small, transparent fix — a versioned DSL with a typed three-tier parameter system — and demonstrates it on the locked routine-activity-theory convergence rule.

## 2. Methods

See `methodology_section.md`. Sections 1–6 are reused verbatim; specific
points emphasised for international reviewers include:

- The synthetic Korean-style grid is a *style* reference, not a real
  Korean city. No real address, no real coordinates, no real
  victimisation data.
- The Civilian Use Policy v1.0 (engine-level) refuses operational
  deployments at the project level, in addition to the per-paper
  ethics declarations.
- The Sobol estimator is implemented from numpy alone (no SALib
  dependency) and is independently validated against the Ishigami
  benchmark.

## 3. Results

### 3.1 Tier-3 exposure on a 5×5 synthetic grid

Default seed 20260427 emits 7 cells with at least one synthetic
opportunity event out of 25. Same-seed reruns produce a
byte-identical ``synthetic_seoul_summary.json`` (SHA-256 invariant).

### 3.2 Sobol sensitivity panel

First-order ≈ 0.23, total-order ≈ 0.54 across motivation, exposure, and
gap. The roughly 30 percent interaction-variance share is the
multiplicative-model signature, validated against the Ishigami benchmark.

### 3.3 CrimeMind weight-regime comparison

Re-implementing the three-slot RAT-prompt structure as Tier C weights
demonstrates that swapping equal weights for motivation-heavy or
guardian-heavy weights redistributes synthetic events without touching
the locked Tier A theory. We do not load CrimeMind's source or data;
this is a patterns-level methodological comparison only.

### 3.4 Pattern-Oriented Modeling 3-gate validation

Three default macro patterns (time-of-day, activity diversity, hotspot
distribution) pass with KS distances all below the configured thresholds
under default Tier C settings.

## 4. Discussion

The proposed three-tier exposure plus deterministic replay is a
practical, light-weight transparency mechanism. It does not require
new statistical machinery, does not require LLM fine-tuning, and does
not depend on any heavyweight optional library; the entire pipeline
runs on numpy and stdlib (with optional GIS / routing / calibration
extras for users who want them).

For international readers we explicitly note: the engine is
**MIT-licensed** (free for civilian research and commercial reuse) but
the Civilian Use Policy refuses the listed defense / predictive-
policing / PSYOP applications regardless of payment.

## 5. Limitations

- Synthetic-grid scenarios cannot demonstrate external predictive
  validity; that is by design and by policy.
- The framework is opinionated about *how* parameters are exposed
  (three tiers, ethics defaults). Adoption requires reviewers to
  internalise the tier semantics.
- LLM-driven decision consistency benchmarks are not within the scope
  of this paper; future work will adopt SOTOPIA-style evaluations.

## References

(Selected; full BibTeX will accompany the manuscript.)

- Cohen LE, Felson M. (1979). *Social change and crime rate trends: A
  routine activity approach.* American Sociological Review.
- Park JS, et al. (2023). *Generative agents: Interactive simulacra of
  human behavior.* arXiv:2304.03442.
- *CrimeMind: Simulating urban crime with multi-modal LLM agents.*
  arXiv:2506.05981, 2025.
- Saltelli A. (2002). *Making best use of model evaluations to compute
  sensitivity indices.* Computer Physics Communications.
- Anderson JR. (2007). *How can the human mind occur in the physical
  universe?* Oxford University Press.
- Grimm V, et al. (2005). *Pattern-oriented modeling of agent-based
  complex systems.* Science.

## Civilian-use statement

This work uses fictional, synthetic, non-identifying scenarios only. It
is not a crime prediction system and does not produce per-person risk
scores. The Luvoire engine on which this study is built declines
defense, predictive-policing, PSYOP, non-consenting real-person
simulation, and minors-in-synthetic-pipelines use categories by
published policy (POLICIES/civilian_use.md, 2026-04-23).
