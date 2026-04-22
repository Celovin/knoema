# Prompt Templates

Luvoire prompt templates support four language codes:

| Code | Language | Surface |
| --- | --- | --- |
| `en` | English | Default system and decision prompts |
| `ko` | Korean | Persona and decision prompts for Korean runs |
| `ja` | Japanese | Persona and decision prompts for Japanese runs |
| `zh` | Chinese | Persona and decision prompts for Chinese runs |

The JSON action schema remains language-neutral across every prompt:

```json
{"action_type": "speak", "target": "agent_id_or_null", "content": "utterance"}
```

This keeps adapters, notebooks, and dashboard ingestion stable even when the natural-language instruction layer changes.

When `Persona.theory_of_mind.enabled` is true and a belief summary is supplied, decision prompts add a `Theory of mind` section without changing the JSON action schema.

## Usage

```python
from luvoire import DecisionEngine, LocalClient, render_persona_system_prompt

prompt = render_persona_system_prompt(persona, language="ko")
engine = DecisionEngine(LocalClient(), language="ko")
```

Accepted aliases include values such as `ko-KR`, `ja-JP`, and `zh-Hans`; internally they normalize to `ko`, `ja`, and `zh`.

## Design Rules

- Keep `Persona ID` unchanged so deterministic local responders and debug tools can parse agent identity.
- Keep JSON keys unchanged: `action_type`, `target`, and `content`.
- Keep theory-of-mind prompt notes opt-in at the persona layer so non-ToM agents do not pay prompt overhead.
- Translate instructions and headings, not data payloads or adapter contracts.
- Add new languages through `src/luvoire/prompts.py` and cover them with tests before using them in examples.
