from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_batch_mm_head_enables_present_mode_query_param() -> None:
    assert "mode\") === \"present\"" in playground_app.APP_HEAD
    assert "present-mode" in playground_app.APP_HEAD
    assert "luvoire-present-hint" in playground_app.APP_HEAD


def test_batch_mm_present_mode_hides_chrome_and_binds_keyboard() -> None:
    assert ".sidebar" in playground_app.APP_HEAD
    assert "display: none !important" in playground_app.APP_HEAD
    assert "ArrowRight" in playground_app.APP_HEAD
    assert "ArrowLeft" in playground_app.APP_HEAD
    assert "Space runs the scenario" in playground_app.APP_HEAD
    assert "Escape" in playground_app.APP_HEAD
    assert "setEditableDisabled" in playground_app.APP_HEAD
