from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _copy_git_visible_tree(source: Path, target: Path) -> None:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=source,
        capture_output=True,
        check=True,
    )
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        rel = Path(raw.decode("utf-8"))
        src = source / rel
        if not src.is_file():
            continue
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _patch_version(worktree: Path, version: str) -> str:
    pyproject_path = worktree / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    current_version = tomllib.loads(pyproject_text)["project"]["version"]
    pyproject_path.write_text(
        pyproject_text.replace(
            f'version = "{current_version}"',
            f'version = "{version}"',
            1,
        ),
        encoding="utf-8",
    )

    init_path = worktree / "src" / "knoema" / "__init__.py"
    init_text = init_path.read_text(encoding="utf-8")
    init_path.write_text(
        init_text.replace(
            f'__version__ = "{current_version}"',
            f'__version__ = "{version}"',
            1,
        ),
        encoding="utf-8",
    )
    return current_version


def run_release_dry_run(version: str, keep: bool = False) -> dict[str, object]:
    if not SEMVER_RE.match(version):
        raise SystemExit(f"Invalid semantic version: {version}")

    root = _repo_root()
    temp_root = Path(tempfile.mkdtemp(prefix="knoema-release-dry-run-"))
    try:
        worktree = temp_root / "worktree"
        dist_dir = temp_root / "dist"
        worktree.mkdir()
        dist_dir.mkdir()
        _copy_git_visible_tree(root, worktree)
        current_version = _patch_version(worktree, version)

        _run([sys.executable, "-m", "build", "--outdir", str(dist_dir)], cwd=worktree)
        dist_paths = sorted(path for path in dist_dir.iterdir() if path.is_file())
        dist_files = [path.name for path in dist_paths]
        if not dist_files:
            raise SystemExit("Build completed without distribution files.")
        _run([sys.executable, "-m", "twine", "check", *[str(path) for path in dist_paths]], cwd=worktree)

        return {
            "status": "ok",
            "current_version": current_version,
            "dry_run_version": version,
            "dist_files": dist_files,
            "kept_path": str(temp_root) if keep else None,
        }
    finally:
        if not keep:
            shutil.rmtree(temp_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and twine-check a temporary release version.")
    parser.add_argument("--version", required=True, help="Semantic version to test, for example 0.1.1.")
    parser.add_argument("--keep", action="store_true", help="Keep the temporary build tree for inspection.")
    args = parser.parse_args()

    result = run_release_dry_run(args.version, args.keep)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = ["run_release_dry_run"]
