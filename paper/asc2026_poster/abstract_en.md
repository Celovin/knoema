# ASC 2026 Methodology Poster Abstract (English)

**Title**: Routine Activity Theory in a Synthetic Korean-Style Urban Grid ABM: Deterministic Replay for Auditable Scenarios

**Submission**: ASC 2026 Annual Meeting, Chicago IL, 2026-11-18 to 2026-11-21
**Submission deadline**: 2026-05-15

## Abstract (300 words)

**Background.** Routine activity theory (RAT) describes crime opportunity as the spatio-temporal convergence of a motivated offender, a suitable target, and the absence of capable guardianship. Translating RAT into a transparent agent-based model (ABM) usually means burying the convergence rule inside opaque code and exposing only numeric knobs, which makes it difficult for reviewers to tell which claims are theoretical, which are empirical, and which are exploratory.

**Methods.** We present a deterministic Python ABM in which the RAT convergence rule is locked as a code-level constant referenced from scenario YAML by a typed string (Tier A), empirical priors must declare their data source (Tier B), and exploration knobs must declare a numeric range and a default (Tier C). Scenarios are loaded by a versioned DSL whose ethics block defaults to ``no_real_geometry: true``: any non-synthetic coordinate-system label is rejected at validation time. Every run is identified by a content hash over scenario YAML, code tree, and seed; replay equality is verified by a five-baseline SHA-256 invariant table that the continuous-integration job re-checks on every push.

**Results.** Across a 4096-sample Saltelli design (20 480 model evaluations, seed = 20260427), Sobol indices for the three RAT components are nearly symmetric — first-order ≈ 0.23 and total-order ≈ 0.54 each — and the gap between total and first-order indices confirms that approximately thirty percent of the output variance is interaction effects, an expected property of the multiplicative convergence rule. Same-seed runs reproduce byte-for-byte across local and CI environments.

**Discussion.** The proposed framework is a methodology poster, not a prediction system. It is fictional, synthetic, and non-identifying by construction; the engine refuses defense, predictive-policing, PSYOP, non-consenting twinning, and minors-in-synthetic-pipelines applications by published policy. We argue that auditable replay plus a tier-typed parameter surface is a practical way to keep RAT-based simulation studies transparent and reviewable.

**Keywords**: routine activity theory; agent-based modeling; auditable replay; sensitivity analysis; reproducibility; synthetic scenarios; civilian-use policy.
