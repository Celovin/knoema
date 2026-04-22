"""Compatibility helpers for the legacy package name."""

from __future__ import annotations

import importlib
import sys
import warnings
from types import ModuleType

_WARNED_FLAG = "_luvoire_legacy_package_warned"


def load_legacy_namespace() -> ModuleType:
    if not getattr(sys, _WARNED_FLAG, False):
        warnings.warn(
            "The 'knoema' package name is deprecated; use 'luvoire'.",
            DeprecationWarning,
            stacklevel=3,
        )
        setattr(sys, _WARNED_FLAG, True)
    return importlib.import_module("luvoire")


__all__ = ["load_legacy_namespace"]
