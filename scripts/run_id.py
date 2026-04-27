"""Compute a Luvoire run identifier from (code, scenario, seed).

The run id is a deterministic SHA-256 over four canonical inputs:

    run_id = SHA256( code_tree_sha || scenario_yaml_sha || seed || pyversion )

where ``code_tree_sha`` is computed over the contents of ``src/luvoire`` (no
__pycache__, no .pyc), ``scenario_yaml_sha`` is the SHA-256 of the loaded
scenario YAML bytes, and ``pyversion`` is ``sys.version_info`` joined with dots.

**Scope and known limitations**:

- The hash covers ``src/luvoire/**/*.py`` only. It deliberately does **not**
  walk ``tests/``, ``pyproject.toml``, ``CHANGELOG.md``, or any other
  repo-root files; a developer who modifies a test fixture or a dependency
  spec without changing source code will produce the same ``run_id``.
  Capture dependency-version drift via ``pip freeze`` piped into ``--env``.
- Third-party package versions are not pinned automatically. Use ``--env``
  to fold a ``pip freeze`` output into ``run_id`` via :func:`env_sha`.
- The hash is stable across machines as long as the ``src/luvoire`` tree
  and the Python major.minor.patch version are identical.

This is the lightest practical replacement for a per-release uv/pixi
lockfile when those tools are unavailable in the working environment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "luvoire"
EXCLUDE_DIRS: frozenset[str] = frozenset({"__pycache__", ".pytest_cache"})


def code_tree_sha(src_dir: Path = SRC_DIR) -> str:
    """SHA-256 over the canonical text content of ``src/luvoire``.

    Files are sorted by path. Each file contributes a line of
    ``path||sha256_of_bytes`` to a single SHA-256 stream so the result is
    stable across reruns and across machines as long as the source tree is
    identical.
    """

    if not src_dir.is_dir():
        raise FileNotFoundError(src_dir)
    digest = hashlib.sha256()
    for path in _iter_python_files(src_dir):
        rel = path.relative_to(src_dir).as_posix()
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        digest.update(f"{rel}||{file_sha}\n".encode())
    return digest.hexdigest()


def scenario_yaml_sha(yaml_path: Path) -> str:
    return hashlib.sha256(yaml_path.read_bytes()).hexdigest()


def env_sha(pip_freeze_lines: Iterable[str]) -> str:
    canonical = sorted(line.strip() for line in pip_freeze_lines if line.strip())
    return hashlib.sha256("\n".join(canonical).encode()).hexdigest()


def compute_run_id(
    *,
    scenario_yaml: Path,
    seed: int,
    pip_freeze_lines: Iterable[str] | None = None,
    src_dir: Path = SRC_DIR,
) -> dict[str, str | int]:
    code_sha = code_tree_sha(src_dir)
    yaml_sha = scenario_yaml_sha(scenario_yaml)
    pyversion = ".".join(str(component) for component in sys.version_info[:3])
    parts = [code_sha, yaml_sha, str(seed), pyversion]
    if pip_freeze_lines is not None:
        parts.append(env_sha(pip_freeze_lines))
    run_id = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return {
        "run_id": run_id,
        "code_tree_sha": code_sha,
        "scenario_yaml_sha": yaml_sha,
        "seed": seed,
        "python_version": pyversion,
    }


def _iter_python_files(src_dir: Path) -> Iterable[Path]:
    for path in sorted(src_dir.rglob("*.py")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--env",
        type=Path,
        help="Optional path to a pip freeze output for env hashing.",
    )
    args = parser.parse_args(argv)
    pip_lines: list[str] | None = None
    if args.env is not None:
        pip_lines = args.env.read_text(encoding="utf-8").splitlines()
    payload = compute_run_id(
        scenario_yaml=args.scenario,
        seed=args.seed,
        pip_freeze_lines=pip_lines,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
