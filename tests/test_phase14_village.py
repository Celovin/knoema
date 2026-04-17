from __future__ import annotations

import json
from pathlib import Path


def _notebook_source(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") in {"markdown", "code"}
    )


def test_phase14_village_notebook_exists_and_documents_goal() -> None:
    notebook_path = Path("examples/04_village.ipynb")

    source = _notebook_source(notebook_path)

    assert "# Experiment: Ten Agent Village Simulation" in source
    assert "exactly 10 personas are active" in source
    assert "240 log entries" in source


def test_phase14_village_notebook_has_ten_agent_scale_checks() -> None:
    source = _notebook_source(Path("examples/04_village.ipynb"))

    assert "assert len(personas) == 10" in source
    assert "assert metrics['agent_count'] == 10" in source
    assert "assert metrics['log_count'] == 240" in source
    assert "assert metrics['relationship_edges'] >= 10" in source
