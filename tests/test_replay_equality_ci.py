"""Smoke test for scripts.replay_equality_ci."""

from __future__ import annotations

import importlib

from scripts import replay_equality_ci


def test_replay_equality_ci_returns_zero() -> None:
    rc = replay_equality_ci.main()
    assert rc == 0


def test_replay_equality_ci_module_exposes_main() -> None:
    importlib.reload(replay_equality_ci)
    assert callable(replay_equality_ci.main)
