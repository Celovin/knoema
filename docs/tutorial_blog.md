# Build a Persistent-Agent Simulation with Knoema

This is a publish-ready tutorial draft for Medium and velog cross-posting. It uses only fictional, synthetic examples and commands that work from a local Knoema checkout.

## Why This Exists

Most LLM agent demos stop at one conversation. Knoema focuses on longer-running social simulations where agents keep memory, relationships, emotion state, and environmental context across ticks.

The MVP is intentionally small:

- Python package for deterministic local runs
- YAML CLI for repeatable scenarios
- Jupyter notebooks for demos
- Streamlit dashboard for replay and live-tail inspection
- Godot adapter scaffold for NPC experiments

## 1. Install From Source

```bash
git clone https://github.com/Celovin/knoema.git
cd knoema
python -m venv .venv
.venv/Scripts/pip install -e ".[dev,dashboard]"
```

On macOS or Linux, use `.venv/bin/pip` instead of `.venv/Scripts/pip`.

## 2. Run a YAML Simulation

Knoema ships with a deterministic dormitory scenario:

```bash
knoema run examples/cli_dorm.yaml --output runs/cli_dorm.jsonl --json
```

The CLI validates the config, creates two fictional agents, runs a one-day simulation, and writes JSONL logs. It uses a local deterministic client by default, so no API key is required.

Use `--dry-run` before handing a scenario to another researcher or developer:

```bash
knoema run examples/cli_dorm.yaml --dry-run --json
```

## 3. Inspect Logs in the Dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`, select the generated JSONL path, and use the playback controls:

- `Live tail` follows the highest tick currently loaded.
- `Trailing ticks` limits the visible window.
- `Auto-refresh` reloads the dashboard while a local JSONL file is growing.

The same playback window drives the agent cards, relationship graph, raw log table, and realtime tab.

## 4. Use Memory Retrieval Diagnostics

The simple memory API returns `Memory` objects:

```python
results = store.retrieve("shared study routine", k=5)
```

For analysis, use scored retrieval:

```python
from knoema import RetrievalWeights

scored = store.retrieve_with_scores(
    "shared study routine",
    k=5,
    weights=RetrievalWeights(semantic=0.65, temporal=0.30, importance=0.05),
)

for result in scored:
    print(result.memory.content, result.final_score)
```

This keeps production code simple while exposing why a memory was selected during experiments.

## 5. Localize the Prompt Layer

The decision prompt layer supports English, Korean, Japanese, and Chinese while keeping the action JSON schema stable.

```python
from knoema import DecisionEngine, LocalClient

engine = DecisionEngine(
    LocalClient(lambda messages: '{"action_type": "observe", "target": null, "content": "notes the routine."}'),
    language="ko",
)
```

This lets you compare behavior under localized persona and decision prompts without changing the simulator, dashboard, or adapters.

## 6. Extend the Scenario

A good next experiment is a ten-agent village:

```bash
jupyter nbconvert --to notebook --execute examples/04_village.ipynb --output tmp/village_executed.ipynb
```

From there, change one variable at a time:

- number of agents
- tick duration
- memory retrieval weights
- prompt language
- scheduled event frequency

Keep outputs in `runs/`, `logs/`, or `tmp/`; those paths are ignored by git.

## Publishing Checklist

- Use only fictional, synthetic people, places, and events.
- Do not include real incident names, victim names, suspect names, or operational data.
- Avoid predictive claims. Frame replay demos as inspection and comparison tools.
- Run `pytest`, `ruff check .`, and `mypy src` before publishing.
- Link to the GitHub repository, CLI docs, prompt docs, and dashboard docs.

## Links

- Repository: `https://github.com/Celovin/knoema`
- CLI docs: `docs/cli.md`
- Prompt docs: `docs/prompts.md`
- Dashboard docs: `dashboard/README.md`
- Research positioning: `docs/research.md`
