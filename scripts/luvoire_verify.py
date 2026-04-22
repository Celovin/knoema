"""CLI shim for Luvoire reproducibility certificate verification."""

from __future__ import annotations

from luvoire.reproducibility import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
