from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

from scripts.verify_replication import ARCHIVE_ENV, EXTRACT_DIR_ENV, REQUIRED_MEMBERS


def test_replication_archive_from_env_contains_required_members() -> None:
    archive_value = os.environ.get(ARCHIVE_ENV)
    extract_value = os.environ.get(EXTRACT_DIR_ENV)
    if not archive_value or not extract_value:
        pytest.skip("replication archive probe runs only from scripts/verify_replication.py")

    archive_path = Path(archive_value)
    extract_dir = Path(extract_value)

    with zipfile.ZipFile(archive_path) as archive:
        members = set(archive.namelist())
        assert set(REQUIRED_MEMBERS).issubset(members)
        manifest = json.loads(
            archive.read("config/reproduction_manifest.json").decode("utf-8")
        )
        assert manifest["source_files"]
        assert archive.read("data/run.jsonl").decode("utf-8").strip()

    assert (extract_dir / "README.md").exists()
    assert (extract_dir / "data" / "run.jsonl").exists()
    assert (extract_dir / "config" / "reproduction_manifest.json").exists()
