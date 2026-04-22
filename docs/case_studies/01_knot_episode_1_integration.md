# Case Study 01: KNOT Episode 1 Integration

> Hypothetical case study. All numbers below are projected from synthetic scenarios, benchmark envelopes, and implementation planning assumptions. They are not claims about a shipped commercial deployment.

## Executive Summary

| Item | Value |
| --- | --- |
| Surface | Narrative game episode with 12 persistent NPCs |
| Engine target | Godot 4 client with Luvoire runtime and dashboard QA |
| Primary problem | Branch explosion and continuity drift across repeat playthroughs |
| Proposed outcome | Memory-aware NPC interactions with reproducible replay logs |
| Evaluation window | 6 weeks from prototype to content lock |

## Background

KNOT Episode 1 is modeled here as a dialogue-heavy narrative short set across a dormitory, hallway, and after-school club room. The design goal is to preserve authored dramatic beats while allowing supporting NPCs to remember prior encounters, carry relationship state across scenes, and react with more variety than a static branching tree can support.

The production constraint is typical for a small narrative team: a few core writers, limited QA bandwidth, and a need to keep the first playable stable enough for external review.

## Problem Statement

The baseline workflow uses hand-authored dialogue trees, state flags, and scene-specific conditionals. That approach keeps deterministic control, but it pushes three problems into the content team:

1. Writers duplicate context in every scene because side characters do not naturally remember prior conversations.
2. QA must manually inspect branch combinations to catch continuity breaks.
3. Late content edits create cascading rewrites because relationship state is scattered across scripts.

## Solution Design

Luvoire is introduced as a supporting runtime rather than a replacement for authored story logic. Critical story beats remain scripted. Persistent NPC responses, memory recall, and low-stakes social interactions move into Luvoire.

```text
Story script triggers
  -> Luvoire persona + relationship state
  -> local or cloud LLM decision
  -> deterministic JSON action record
  -> Godot presentation layer
  -> dashboard review and replay QA
```

### Proposed Integration Scope

- 12 named NPCs with seeded persona files and relationship defaults
- 3 high-traffic locations wired to shared environment context
- 18 repeatable social beats delegated to Luvoire
- 1 authored climax path left fully script-driven
- nightly replay export for narrative QA

## Timeline

| Week | Deliverable | Owner focus |
| --- | --- | --- |
| 1 | Persona roster, scene boundaries, replay acceptance sheet | Narrative + design |
| 2 | Godot adapter hookup and first hallway encounter | Engine |
| 3 | Memory tuning for dorm and club scenes | Engine + writing |
| 4 | Dashboard QA pass, regression replay pack | QA |
| 5 | Content lock candidate and fallback rules | Narrative |
| 6 | External review build and trace archive | Production |

## Projected Metrics

| Metric | Baseline | Luvoire target | Why it matters |
| --- | --- | --- | --- |
| Writer-authored variant lines per side scene | 140 | 85 | More reuse through memory-aware responses |
| Continuity QA checks per build | 22 | 10 | Replay logs reduce manual verification loops |
| Side-character recall accuracy in scripted test prompts | 58% | 88% | Better narrative continuity for returning scenes |
| Branch maintenance hours per milestone | 30h | 18h | Fewer duplicated state checks |
| Replay turnaround from bug report to verified fix | 1.5 days | 4 hours | JSONL replay shortens repro time |

## Success Metrics

- External reviewer can replay the same seed and see the same high-level social arc.
- NPCs remember at least one prior encounter in each repeatable scene cluster.
- Story-critical scenes remain stable even when non-critical social behavior varies.
- Designers can inspect relationship changes without opening raw save data.

## Evidence Pack for Review

- Godot scene capture of the hallway introduction
- Dashboard screenshot showing relationship drift over three scenes
- JSONL replay artifact for one full episode seed
- Scenario DSL file for the dorm orientation beat

## Risks and Guardrails

| Risk | Guardrail |
| --- | --- |
| NPC improvisation collides with authored canon | Keep climax and irreversible plot beats fully scripted |
| LLM latency disrupts scene pacing | Use local deterministic fallback for QA and low-stakes previews |
| Writer trust drops if behavior is opaque | Require replay links and retrieval diagnostics in review |
| Scope creep into fully procedural storytelling | Freeze integration to support scenes, not main plot replacement |

## Decision

This case study supports a narrow, realistic integration thesis: Luvoire is most valuable when it handles continuity-heavy support interactions while the game keeps authored control over pacing, revelation, and finale structure.
