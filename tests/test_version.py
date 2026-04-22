"""Smoke test to confirm the package imports and exposes a version string."""

from __future__ import annotations

import luvoire


def test_version_is_string() -> None:
    assert isinstance(luvoire.__version__, str)
    assert luvoire.__version__.count(".") >= 1
