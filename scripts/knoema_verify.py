"""CLI shim for Knoema reproducibility certificate verification."""

from __future__ import annotations

from knoema.reproducibility import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
