# Case Study 03: Indie Studio Adoption

> Hypothetical case study. The rollout below models an indie studio evaluation path and forecast metrics. It is not a statement about a signed customer, shipped title, or measured production uplift.

## Executive Summary

| Item | Value |
| --- | --- |
| Surface | Korean indie studio adding persistent social NPC behavior |
| Engine target | Unity or Godot game loop with Knoema SDK facade |
| Primary problem | Static dialogue trees create content bottlenecks and low replay variety |
| Proposed outcome | Memory-aware NPC layer with controlled integration cost |
| Adoption window | 10-week evaluation from prototype to vertical slice |

## Background

Small studios often want richer NPC behavior but cannot afford a full live-ops AI team. They need an integration that fits their shipping reality: low engineering overhead, predictable cost, and the ability to fall back to deterministic local behavior during development.

The studio modeled here is building a relationship-driven game with a central town hub, rotating quests, and a cast of 20 recurring NPCs.

## Problem Statement

The studio's existing content stack relies on handcrafted dialogue trees and quest flags. That keeps scope controlled, but it limits replayability and increases maintenance cost as the cast grows.

The team wants:

1. More varied NPC responses without rewriting every branch.
2. A single runtime that can support both gameplay scripting and QA replay.
3. A staged adoption plan that does not block the current vertical-slice milestone.

## Solution Design

Knoema enters as an SDK-layer augmentation around existing quest systems. The studio keeps authored quest state, but delegates ambient social behavior, memory recall, and low-risk side conversations to Knoema.

```text
Quest state + world events
  -> SDK facade
  -> Knoema persona and relationship state
  -> local or hosted inference
  -> game response payload
  -> replay and dashboard QA
```

### Adoption Scope

- 20 recurring NPCs with shared town-hub memory
- 6 quest-adjacent side conversations delegated to Knoema
- 1 live vertical-slice scene with deterministic QA fallback
- Python and TypeScript tooling for content iteration
- Unity or Godot adapter chosen by the studio's engine branch

## Timeline

| Phase | Duration | Deliverable |
| --- | --- | --- |
| Prototype | Weeks 1-2 | One NPC, one quest hub, replay capture |
| Content fit | Weeks 3-5 | Persona roster, memory tuning, side-scene review |
| Vertical slice | Weeks 6-8 | 6 integrated scenes, fallback path, QA scripts |
| Go/no-go | Weeks 9-10 | Cost review, retention hypothesis, backlog decision |

## Projected Metrics

| Metric | Baseline | Adoption target | Why it matters |
| --- | --- | --- | --- |
| Authoring time per support NPC | 8h | 5h | Fewer unique branches to script manually |
| Distinct side-scene response variants | 1.0x | 2.8x | Better replay value |
| QA repro time for social-state bugs | 1 day | 2 hours | Replayable traces and dashboard inspection |
| Vertical-slice content change lead time | 5 days | 3 days | More isolated behavior layer |
| Forecast day-7 retention impact | flat | +4% to +7% | More social novelty in repeat sessions |

## Success Metrics

- The studio can ship one vertical-slice build with both live inference and deterministic fallback.
- Designers can adjust persona traits without touching quest logic.
- NPC state changes remain reviewable through exported logs.
- Cost review stays within the studio's monthly AI budget envelope.

## Evidence Pack for Review

- Vertical-slice capture of an NPC hub interaction
- SDK integration snippet and persona file example
- Replay log showing the same seed across two QA runs
- Budget sheet comparing local fallback and hosted inference modes

## Risks and Guardrails

| Risk | Guardrail |
| --- | --- |
| Players see inconsistent quest-critical dialog | Reserve quest progression text for authored scripts |
| Cost spikes during playtesting | Default to local fallback for QA and nightly runs |
| Designers overfit prompts per NPC | Use shared templates with only persona deltas |
| Studio expects fully autonomous storytelling | Limit adoption to ambient and side-scene interactions |

## Decision

For indie teams, Knoema is strongest as a replayable social-behavior layer that sits beside existing quest logic. The adoption path becomes credible when integration is incremental, fallback is deterministic, and success is measured against authoring speed plus replay value, not hype.
