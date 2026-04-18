---
title: Knoema Playground
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# Knoema Playground

Interactive browser demo for Knoema Engine, a multi-agent social simulation engine for games,
public-safety research, and academic experiments.

## What It Does

- Choose one of three scenario presets:
  - Dorm: two agents
  - Village: ten agents
  - School corridor
- Run a deterministic replay without an API key.
- Optionally provide an OpenAI or Anthropic API key for a live LLM-backed run.
- Customize the primary agent's name, age, and Big Five personality values.
- Inspect a tick-by-tick timeline.
- View the relationship graph.
- Download the JSONL simulation log.

API keys are passed only to the selected SDK client for the current request. The app does not
write keys to disk or store them in module-level state.

## Local Run

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\pip install -r playground\requirements.txt
.venv\Scripts\python playground\app.py
```

## Hugging Face Space Deployment

1. Create a new public Space named `Celovin/knoema-playground`.
2. Select the Gradio SDK.
3. Upload the contents of this `playground/` directory.
4. Wait for the Space build to install `requirements.txt`.
5. Open the Space and run `Replay only` mode first.

Target URL:

```text
https://huggingface.co/spaces/Celovin/knoema-playground
```

## No-Key Demo Path

Use `Replay only`, select `Dorm: two agents`, keep the defaults, and press **Run simulation**.
The first timeline entries should appear immediately because the local deterministic responder is
used instead of an external model.

## Live Model Path

1. Select `OpenAI` or `Anthropic`.
2. Paste your API key into the password field.
3. Set a model name such as `gpt-4o-mini` or `claude-3-5-haiku-latest`.
4. Run 1-4 ticks first to keep cost low.

The JSONL log can be downloaded after every run.
