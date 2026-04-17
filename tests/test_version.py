"""Smoke test to confirm the package imports and exposes a version string."""

from __future__ import annotations

import knoema


def test_version_is_string() -> None:
    assert isinstance(knoema.__version__, str)
    assert knoema.__version__.count(".") >= 1
