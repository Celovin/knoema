# Fine-tuning Dataset Export

Knoema run logs can be converted into chat fine-tuning records for OpenAI-style JSONL, Anthropic-style JSONL, or DPO preference pairs.

## Python API

```python
from pathlib import Path
from knoema.export import export_finetuning_jsonl, to_openai_jsonl

jsonl_text = Path("runs/demo.jsonl").read_text(encoding="utf-8")
records = to_openai_jsonl(jsonl_text)
Path("runs/openai_finetuning.jsonl").write_text(
    export_finetuning_jsonl(jsonl_text, "openai"),
    encoding="utf-8",
)
```

Each row keeps the source `agent_id`, `tick`, timestamp, and action type in metadata. The assistant response is the canonical JSON action payload, so downstream jobs can learn action selection rather than free-form summaries.

## Formats

- `openai`: `{"messages": [...]}` chat records.
- `anthropic`: `{"system": "...", "messages": [...]}` chat records.
- `dpo`: preference pairs with `messages`, `chosen`, and `rejected`. Pass a second run log as `rejected_run_log` to compare two runs; otherwise the exporter builds a conservative wait-action baseline.

## Playground

After a run, use the fine-tuning export controls in the Result exports panel:

1. Choose OpenAI, Anthropic, or DPO.
2. Click Export fine-tuning dataset.
3. Download the generated JSONL file.

The exporter works on the current JSONL log and does not send data to an external provider.
