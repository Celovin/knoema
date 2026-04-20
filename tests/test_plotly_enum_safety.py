from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")

# Official Plotly references used for the enum whitelist:
# https://plotly.com/python/reference/scatter/
# https://plotly.com/python/reference/scatter3d/
# https://plotly.com/python/reference/bar/
APP_SOURCE_PATH = Path("playground/app.py")
SCATTER_MODE_WHITELIST = {
    "lines",
    "markers",
    "text",
    "lines+markers",
    "lines+text",
    "markers+text",
    "lines+markers+text",
    "none",
}
SCATTER3D_SYMBOL_WHITELIST = {
    "circle",
    "circle-open",
    "cross",
    "diamond",
    "diamond-open",
    "square",
    "square-open",
    "x",
}
BAR_PATTERN_SHAPE_WHITELIST = {"", "/", "\\", "x", "-", "|", "+", "."}


def _graph_object_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    if not isinstance(node.func.value, ast.Name):
        return None
    if node.func.value.id != "go":
        return None
    return node.func.attr


def _constant_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _dict_string_value(node: ast.AST, *keys: str) -> str | None:
    current = node
    for key in keys:
        if not isinstance(current, ast.Dict):
            return None
        next_value: ast.AST | None = None
        for dict_key, dict_value in zip(current.keys, current.values, strict=True):
            if _constant_string(dict_key) == key:
                next_value = dict_value
                break
        if next_value is None:
            return None
        current = next_value
    return _constant_string(current)


def test_plotly_scatter_modes_in_playground_app_are_whitelisted() -> None:
    tree = ast.parse(APP_SOURCE_PATH.read_text(encoding="utf-8"))
    discovered_modes: set[str] = set()
    for node in ast.walk(tree):
        graph_name = _graph_object_name(node)
        if graph_name not in {"Scatter", "Scatter3d"}:
            continue
        for keyword in getattr(node, "keywords", []):
            if keyword.arg != "mode":
                continue
            mode = _constant_string(keyword.value)
            if mode is not None:
                discovered_modes.add(mode)
    assert discovered_modes
    assert discovered_modes <= SCATTER_MODE_WHITELIST


def test_plotly_scatter3d_marker_symbols_in_playground_app_are_whitelisted() -> None:
    tree = ast.parse(APP_SOURCE_PATH.read_text(encoding="utf-8"))
    discovered_symbols: set[str] = set()
    for node in ast.walk(tree):
        graph_name = _graph_object_name(node)
        if graph_name != "Scatter3d":
            continue
        for keyword in getattr(node, "keywords", []):
            if keyword.arg != "marker":
                continue
            symbol = _dict_string_value(keyword.value, "symbol")
            if symbol is not None:
                discovered_symbols.add(symbol)
    assert discovered_symbols
    assert discovered_symbols <= SCATTER3D_SYMBOL_WHITELIST


def test_plotly_action_pattern_sequence_matches_bar_pattern_shape_whitelist() -> None:
    assert set(playground_app.ACTION_PATTERN_SEQUENCE) == BAR_PATTERN_SHAPE_WHITELIST
    assert len(playground_app.ACTION_PATTERN_SEQUENCE) == 8
    assert len(set(playground_app.ACTION_PATTERN_SEQUENCE)) == 8


def test_plotly_action_pattern_cycle_wraps_after_eight_action_types() -> None:
    action_types = [f"action_{index:02d}" for index in range(9)]
    breakdown: dict[str, dict[str, int]] = {
        "agent_1": {action_type: index + 1 for index, action_type in enumerate(action_types)}
    }

    figure = playground_app._action_chart_figure(breakdown, language="en")
    pattern_shapes = [trace.marker.pattern.shape for trace in figure.data]

    assert len(pattern_shapes) == len(action_types)
    assert pattern_shapes[:8] == list(playground_app.ACTION_PATTERN_SEQUENCE)
    assert pattern_shapes[8] == playground_app.ACTION_PATTERN_SEQUENCE[0]
