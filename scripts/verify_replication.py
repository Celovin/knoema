"""Verify a Knoema replication package archive."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ARCHIVE_ENV = "KNOEMA_REPLICATION_ARCHIVE"
EXTRACT_DIR_ENV = "KNOEMA_REPLICATION_EXTRACT_DIR"
PYTEST_TARGET = "tests/reproducibility/test_replication_package_verify.py"
REQUIRED_MEMBERS = (
    "README.md",
    "data/run.jsonl",
    "data/summary.txt",
    "config/reproduction_manifest.json",
    "config/environment-freeze.txt",
    "notebooks/reproduce_run.ipynb",
    "source/pyproject.toml",
    "source/playground/app.py",
)


def inspect_replication_archive(archive_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(archive_path) as archive:
        members = tuple(sorted(archive.namelist()))
        member_set = set(members)
        missing_members = [member for member in REQUIRED_MEMBERS if member not in member_set]
        manifest = json.loads(
            archive.read("config/reproduction_manifest.json").decode("utf-8")
        )
        jsonl_rows = [
            line
            for line in archive.read("data/run.jsonl").decode("utf-8").splitlines()
            if line.strip()
        ]
        return {
            "member_count": len(members),
            "missing_members": missing_members,
            "jsonl_row_count": len(jsonl_rows),
            "manifest_keys": sorted(manifest),
        }


def verify_replication_package(archive_path: Path, *, run_pytest: bool = True) -> dict[str, Any]:
    resolved_archive = archive_path.expanduser().resolve()
    if not resolved_archive.exists():
        raise FileNotFoundError(f"archive not found: {resolved_archive}")

    report = inspect_replication_archive(resolved_archive)
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="knoema-replication-verify-") as temp_dir:
        extract_dir = Path(temp_dir)
        with zipfile.ZipFile(resolved_archive) as archive:
            archive.extractall(extract_dir)

        report.update(
            {
                "archive_path": str(resolved_archive),
                "extract_dir": str(extract_dir),
                "pytest_target": PYTEST_TARGET,
            }
        )

        if run_pytest:
            env = os.environ.copy()
            env[ARCHIVE_ENV] = str(resolved_archive)
            env[EXTRACT_DIR_ENV] = str(extract_dir)
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", PYTEST_TARGET, "-q"],
                cwd=repo_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            report["pytest_exit_code"] = completed.returncode
            report["pytest_stdout"] = completed.stdout.strip()
            report["pytest_stderr"] = completed.stderr.strip()
        else:
            report["pytest_exit_code"] = None
            report["pytest_stdout"] = ""
            report["pytest_stderr"] = ""

    report["verification_passed"] = bool(
        not report["missing_members"]
        and (report["pytest_exit_code"] in {0, None})
        and int(report["jsonl_row_count"]) > 0
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Knoema replication package zip.")
    parser.add_argument("archive", help="Path to the replication package zip")
    args = parser.parse_args()

    try:
        report = verify_replication_package(Path(args.archive))
    except Exception as exc:  # pragma: no cover - CLI failure path
        print("verification_passed: false", file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"verification_passed: {'true' if report['verification_passed'] else 'false'}")
    print(f"archive_path: {report['archive_path']}")
    print(f"extract_dir: {report['extract_dir']}")
    print(f"member_count: {report['member_count']}")
    print(f"jsonl_row_count: {report['jsonl_row_count']}")
    print(f"missing_members: {', '.join(report['missing_members']) or 'none'}")
    print(f"pytest_target: {report['pytest_target']}")
    if report["pytest_exit_code"] is not None:
        print(f"pytest_exit_code: {report['pytest_exit_code']}")
    if report["pytest_stdout"]:
        print(report["pytest_stdout"])
    if report["pytest_stderr"]:
        print(report["pytest_stderr"], file=sys.stderr)
    return 0 if report["verification_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
