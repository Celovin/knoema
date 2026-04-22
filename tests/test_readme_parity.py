from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_readme_parity_check_passes_for_all_locales() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/check_readme_parity.py"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
