# Competitor Matrix

Last reviewed: 2026-04-19

This matrix compares Knoema Engine with academic generative-agent systems, agent orchestration frameworks, game NPC platforms, and traditional agent-based modeling tools. The intent is positioning, not a vendor benchmark. Items marked as `partial` mean the capability can be built or approximated but is not a first-class public surface in the referenced project.

## Summary

**Knoema Only:** among the compared tools, Knoema is the only public repo in this matrix that combines an MIT license, LLM-native social simulation, persistent memory, a directed relationship graph, persona opt-in theory-of-mind tracking, JSONL replay logs, Korean-capable prompt templates, and both Godot plus Unity adapter scaffolds.

| Project / Product | Category | LLM-native | Game engine integration | Persistent memory and relationships | Theory of mind surface | Relationship graph model | Reproducible experiment surface | Korean first-class support | License / access | Deployment shape |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Knoema Engine | Open-source engine | Yes | Godot and Unity scaffolds | Yes | Yes, persona opt-in symbolic belief tracker with deterministic Sally-Anne harness | Yes, directed trust/familiarity graph | Yes, YAML config, deterministic local client, JSONL logs | Yes, prompt templates include Korean | MIT | Local Python, notebooks, dashboard, adapters, Playground-ready |
| Stanford Generative Agents | Academic prototype | Yes | No packaged game SDK | Yes, memory stream and reflection architecture | Partial, public materials describe memory and reflection but do not expose an opt-in ToM API or Sally-Anne score | Partial, emergent social behavior rather than standalone graph API | Partial, paper and demo code | No | MIT code repository | Local research prototype |
| Google DeepMind Concordia | Academic / research library | Yes | No packaged Unity/Godot SDK | Yes, component-based generative agents | Partial, public materials describe grounded agent reasoning but do not expose an opt-in ToM API or Sally-Anne score | Partial, mediated by game-master style components | Partial, scenario code and PyPI package | No | Apache-2.0 | Local Python package |
| Microsoft AutoGen | Agent orchestration framework | Yes | No game SDK | Partial, application-defined | No first-class social-belief surface | No first-class social relationship graph | Partial, app-dependent | No | MIT code, CC-BY docs | Python packages and app framework |
| OpenAI Swarm | Educational orchestration framework | Yes | No | No | No first-class social-belief surface | No | Partial, examples/tests | No | MIT | Local cookbook-style framework |
| Inworld AI | Commercial game AI platform | Yes | Unity and Unreal runtime SDKs | Proprietary platform capability | Proprietary character reasoning, no public reproducible ToM benchmark | Not publicly exposed as a reproducible graph model | No public experiment replay contract | No | Commercial SDK agreement | Cloud plus engine SDKs |
| Convai | Commercial game NPC platform | Yes | Unity and Unreal plugins | Proprietary character/knowledge system | Proprietary character reasoning, no public reproducible ToM benchmark | No public graph model | No public experiment replay contract | No | Commercial / closed platform | Cloud plus engine plugins |
| Character.AI | Consumer character platform | Yes | No official public API | Hosted character experience | No public developer ToM surface | No developer graph API | No | No | Closed hosted service | Web and mobile app |
| Mesa | Traditional ABM framework | No | No game SDK | User-defined | User-defined | User-defined | Yes, Python models and seeds | No | Apache-2.0 | Local Python, browser visualization |
| AnyLogic | Commercial simulation suite | No | No game SDK | User-defined | User-defined | User-defined | Yes, model-file based | No | Proprietary commercial | Desktop and exported models |
| NetLogo | Traditional ABM environment | No | No game SDK | User-defined | User-defined | User-defined | Yes, model files | No | Open source with commercial license option | Desktop and web variants |

## Notes

- Stanford Generative Agents introduced memory, reflection, and planning patterns for believable behavior in a 25-agent sandbox, but the cited public materials do not expose a persona opt-in theory-of-mind API or a public Sally-Anne benchmark score.
- Concordia is close on generative social simulation, but the cited public materials do not expose a persona opt-in theory-of-mind API, a public Sally-Anne benchmark score, game-engine adapters, or Korean-first prompt surfaces.
- AutoGen and Swarm are orchestration frameworks, not persistent social-world simulators.
- Inworld and Convai are strongest on game-engine delivery, but they are commercial hosted platforms rather than reproducible open research engines.
- Mesa, AnyLogic, and NetLogo remain strong ABM baselines, but they are not LLM-native and do not include persistent natural-language memory by default.

## Sources

- Knoema Engine repository: <https://github.com/Celovin/knoema>
- Stanford Generative Agents paper: <https://arxiv.org/abs/2304.03442>
- Stanford generative agents code repository: <https://github.com/joonspk-research/genagents>
- Google DeepMind Concordia repository: <https://github.com/google-deepmind/concordia>
- Microsoft AutoGen repository: <https://github.com/microsoft/autogen>
- OpenAI Swarm repository: <https://github.com/openai/swarm>
- Inworld Unity runtime quickstart: <https://docs.inworld.ai/Unity/runtime/get-started>
- Inworld SDK license: <https://inworld.ai/sdk-license>
- Convai Unity plugin documentation: <https://docs.convai.com/api-docs/plugins-and-integrations/unity-plugin>
- Character.AI API support note: <https://support.character.ai/hc/en-us/articles/15063996838299-Is-there-an-API>
- Mesa documentation: <https://mesa.readthedocs.io/stable/>
- AnyLogic professional feature page: <https://www.anylogic.com/anylogic-professional>
- NetLogo copyright and license information: <https://docs.netlogo.org/copyright.html>
