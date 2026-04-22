# Case Study 02: Korean University Pilot

> Hypothetical case study. This document describes a synthetic research pilot and projected operating metrics. It does not represent a live university deployment or real participant data.

## Executive Summary

| Item | Value |
| --- | --- |
| Surface | University lab pilot for synthetic social-simulation research |
| Study format | 30 replayable YAML scenarios over 8 weeks |
| Primary problem | Reproducible social experiments are hard to share across notebooks and dashboards |
| Proposed outcome | Versioned scenarios, deterministic replays, and inspectable memory/relationship traces |
| Safety posture | Synthetic agents only, no real student records, no predictive use |

## Background

Many university labs can prototype social simulations in notebooks, but struggle to move from one-off demos to repeatable research assets. Scenario definitions drift, logging formats change, and student assistants cannot easily compare runs across seeds or parameter changes.

The modeled pilot here targets a Korean university research group interested in campus adaptation, orientation stress, peer feedback, and volunteer coordination. Every scenario remains synthetic and non-identifying.

## Problem Statement

The lab needs one workflow that can satisfy both exploratory research and review requirements:

1. Scenario definitions must be versionable and readable by non-engineers.
2. Repeat runs must preserve seed-level reproducibility for audit and paper writing.
3. Reviewers need a dashboard that surfaces memory recall and relationship evolution without reading raw logs.

## Solution Design

Luvoire provides a single path from YAML scenario design to replayable simulation output, benchmark evidence, and export-ready documentation.

```text
Research question
  -> Scenario DSL authoring
  -> validator and ethics guardrails
  -> deterministic simulation run
  -> dashboard inspection
  -> report appendix and citation export
```

### Pilot Scope

- 30 curated scenarios across dorm life, classroom teamwork, and campus operations
- 3 scenario families re-run with 5 seed variants each
- 1 weekly review meeting based on exported replay summaries
- 1 reproducibility appendix template per experiment family

## Timeline

| Week | Deliverable | Review point |
| --- | --- | --- |
| 1 | Research questions, scenario inventory, ethics checklist | Lab kickoff |
| 2 | YAML authoring workshop and validator onboarding | Scenario sign-off |
| 3 | First reproducibility batch with five seeds | Methods review |
| 4 | Dashboard walkthrough and retrieval diagnostics | Mid-pilot check |
| 5 | Expanded scenario pack and comparison notebook | PI review |
| 6 | Draft appendix figures and benchmark notes | Writing sync |
| 7 | Final synthetic replay package | Internal presentation |
| 8 | Submission-ready archive and handoff | Pilot close |

## Projected Metrics

| Metric | Baseline | Pilot target | Why it matters |
| --- | --- | --- | --- |
| Same-seed rerun agreement | ad hoc | 10/10 identical summary outputs | Reviewable reproducibility |
| Scenario author onboarding time | 2 days | 3 hours | DSL lowers setup cost |
| Replay inspection time per run | 45 min | 12 min | Dashboard reduces log digging |
| Methods appendix preparation | 3 days | 1 day | Exportable artifacts and tables |
| Sensitive-data exposure risk | medium | zero real-person data | Fits synthetic-only boundary |

## Success Metrics

- Every pilot scenario passes the ethics validator before execution.
- The lab can reproduce a selected result from config, seed, and JSONL artifact only.
- Review meetings use replay links instead of notebook screenshots.
- Final write-up includes explicit limitations around synthetic data and non-predictive scope.

## Evidence Pack for Review

- Scenario DSL samples for dorm orientation and peer feedback
- Dashboard capture of memory inspection and relationship explorer
- Reproducibility report excerpt with same-seed rerun summary
- Citation export and appendix-ready result tables

## Risks and Guardrails

| Risk | Guardrail |
| --- | --- |
| Researchers drift toward real student narratives | Require fictionalized composites and non-identifying entities |
| Pilot becomes a prediction tool by expectation | Frame all outputs as replay and hypothesis-comparison artifacts |
| Results are too hard for reviewers to interpret | Standardize scenario cards and summary metrics across runs |
| Too much time is spent on bespoke tooling | Keep the pilot on existing CLI, dashboard, and docs surfaces |

## Decision

This pilot is strongest when positioned as a reproducible synthetic research workflow. Its value is not operational prediction. Its value is faster iteration, stronger auditability, and cleaner handoff from scenario design to evidence.
