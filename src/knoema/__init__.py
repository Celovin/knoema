from __future__ import annotations

import importlib

_compat = importlib.import_module(__name__ + "_compat")
_target = _compat.load_legacy_namespace()

for _key, _value in vars(_target).items():
    if _key not in {"__loader__", "__name__", "__package__", "__spec__"}:
        globals()[_key] = _value

__all__ = getattr(_target, "__all__", [])
__path__ = _target.__path__
