from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
prereg_templates = importlib.import_module("playground.prereg_templates")

TEMPLATE_DIR = Path("docs/research/prereg_templates")
REQUIRED_SECTIONS = (
    "## Research Question",
    "## Hypotheses",
    "## IV/DV",
    "## Sample Size",
    "## Analysis Plan",
    "## Submission Checklist",
)


def test_batch_hh_prereg_template_docs_cover_required_library() -> None:
    template_files = sorted(TEMPLATE_DIR.glob("*.md"))
    template_ids = {
        template.template_id
        for template in prereg_templates.PREREG_TEMPLATES
    }

    assert len(template_files) == 10
    assert {path.stem for path in template_files} == template_ids
    for path in template_files:
        text = path.read_text(encoding="utf-8")
        assert path.stem in template_ids
        for section in REQUIRED_SECTIONS:
            assert section in text


def test_batch_hh_prereg_template_dropdown_autofills_osf_fields() -> None:
    updates = playground_app._prereg_template_updates(
        "memory_decay_retrieval_accuracy",
        "English",
    )

    assert "Memory decay" in updates[0]
    assert "Longer simulated delay" in updates[1]
    assert "Delay window" in updates[4]
    assert updates[10] == 200.0
    assert updates[11] == "paired_t"
    assert "Recommended total sample size" in updates[-1]


def test_batch_hh_playground_exposes_template_picker() -> None:
    app = playground_app.build_app()
    elem_ids = {
        getattr(component, "elem_id", None)
        for component in app.blocks.values()
    }

    assert "prereg-template-picker" in elem_ids
    assert len(prereg_templates.prereg_template_choices("en")) == 10
    assert len(prereg_templates.prereg_template_choices("ko")) == 10
