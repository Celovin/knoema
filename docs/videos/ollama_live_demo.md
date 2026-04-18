# Ollama Live Demo Cue Sheet

Goal: capture one clean five-agent live Ollama run with `llama3.1:8b` and a visible 30-second cap.

Note: as of April 19, 2026, the official Ollama library lists `llama3.3` as a 70B family entry. The 8B live path in this repo therefore uses the official `llama3.1:8b` model.

## Recording Setup

- Working directory: `C:\Users\admin\Projects\knoema`
- Ollama server: `ollama serve`
- Required model: `ollama pull llama3.1:8b`
- Notebook: `examples/05_live_ollama_demo.ipynb`
- Screen crop: terminal plus notebook result cell, no secrets or unrelated windows

## Cue Sheet

| Time | Shot | Notes |
| --- | --- | --- |
| 0:00-0:05 | Title cell | Show `llama3.1:8b`, seeded five-agent setup, and the one-tick live path. |
| 0:05-0:10 | Environment cell | Confirm the notebook can see the model list and the fixed seed `20260419`. |
| 0:10-0:18 | Run cell starts | Start the timer and execute `run_live_ollama_demo(...)`. Keep the output cell in frame. |
| 0:18-0:24 | Result JSON | Pause on elapsed seconds, action count, relationship edges, and action mix. |
| 0:24-0:30 | JSONL preview | Scroll just enough to show one or two structured action rows. |

## Acceptance Check

- The live run uses exactly five agents.
- The live run targets `llama3.1:8b`.
- The elapsed time stays under the 30-second cap.
- The result includes 5 actions, one per agent, plus a JSONL preview.

## Operator Notes

- If the model is missing, pull it before recording and rerun the environment check cell.
- If the live run exceeds 30 seconds, lower local load, close other GPU-heavy apps, and rerun the notebook kernel from the top.
- If Ollama is reachable but the model name differs locally, set `KNOEMA_OLLAMA_LIVE_MODEL` before launching Jupyter and keep the notebook output visible.
