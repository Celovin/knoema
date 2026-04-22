from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def test_sbom_build_is_repeatable_and_checkable() -> None:
    command = [sys.executable, "scripts/build_sbom.py"]
    subprocess.run(command, cwd=ROOT, check=True)
    first = (ROOT / "sbom.cdx.json").read_bytes()
    subprocess.run(command, cwd=ROOT, check=True)
    second = (ROOT / "sbom.cdx.json").read_bytes()

    assert first == second
    subprocess.run([*command, "--check"], cwd=ROOT, check=True)


def test_sbom_is_cyclonedx_15_and_covers_runtime_dependencies() -> None:
    data = json.loads((ROOT / "sbom.cdx.json").read_text(encoding="utf-8"))
    _assert_minimal_cyclonedx_15(data)

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_names = {
        canonicalize_name(Requirement(requirement).name)
        for requirement in pyproject["project"]["dependencies"]
    }
    component_names = {canonicalize_name(component["name"]) for component in data["components"]}

    assert runtime_names <= component_names


def test_sbom_has_license_supplier_and_no_author_email_leak() -> None:
    data = json.loads((ROOT / "sbom.cdx.json").read_text(encoding="utf-8"))

    for component in data["components"]:
        assert component["supplier"]["name"]
        assert component["licenses"][0]["license"]
    assert re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", json.dumps(data)) is None


def _assert_minimal_cyclonedx_15(data: dict[str, Any]) -> None:
    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.5"
    assert isinstance(data["version"], int)
    assert isinstance(data["components"], list)
    for component in data["components"]:
        assert component["type"] == "library"
        assert component["name"]
        assert component["version"]
        assert component["purl"].startswith(("pkg:pypi/", "pkg:npm/"))
        assert component["licenses"]

