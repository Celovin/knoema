# Knoema Dashboard

Streamlit dashboard for inspecting Knoema simulation JSONL exports.

## Run

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\pip install -e ".[dashboard]"
.venv\Scripts\streamlit run dashboard\app.py
```

Open `http://localhost:8501`.

## Input

Use one of these sources:

- Bundled sample: `dashboard\sample_simulation.jsonl`
- Uploaded JSONL file from `Simulator.export_logs(...)`
- Local JSONL path

The dashboard expects one JSON object per line in the format produced by `SimulationLogEntry.to_json_dict()`.
