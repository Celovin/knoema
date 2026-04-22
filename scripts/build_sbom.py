"""Build a deterministic CycloneDX 1.5 SBOM for Luvoire."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sbom.cdx.json"
UNKNOWN_VERSION = "0+unknown"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if sbom.cdx.json is stale")
    args = parser.parse_args(argv)

    rendered = json.dumps(build_sbom(ROOT), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit("sbom.cdx.json is missing; run scripts/build_sbom.py")
        current = OUTPUT.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit("sbom.cdx.json is stale; run scripts/build_sbom.py")
        return

    OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")


def build_sbom(root: Path) -> dict[str, Any]:
    project = _read_pyproject(root)
    components = _collect_python_components(root, project)
    components.extend(_collect_node_components(root))
    components = sorted(_dedupe_components(components), key=lambda item: (item["name"], item["version"]))
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "metadata": {
            "component": {
                "name": project["project"]["name"],
                "type": "application",
                "version": project["project"]["version"],
            },
            "tools": [
                {
                    "name": "scripts/build_sbom.py",
                    "vendor": "Celovin",
                    "version": "1",
                }
            ],
        },
        "specVersion": "1.5",
        "version": 1,
        "components": components,
    }


def _read_pyproject(root: Path) -> dict[str, Any]:
    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))


def _collect_python_components(root: Path, project: dict[str, Any]) -> list[dict[str, Any]]:
    requirement_names: set[str] = set()
    for requirement in project["project"].get("dependencies", []):
        requirement_names.add(_requirement_name(requirement))
    for path in sorted(root.rglob("requirements*.txt")):
        if ".venv" in path.parts:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                requirement_names.add(_requirement_name(stripped))

    return [_python_component(name) for name in sorted(requirement_names)]


def _requirement_name(requirement: str) -> str:
    try:
        return canonicalize_name(Requirement(requirement).name)
    except Exception:
        match = re.match(r"([A-Za-z0-9_.-]+)", requirement)
        if not match:
            raise ValueError(f"cannot parse requirement: {requirement}") from None
        return canonicalize_name(match.group(1))


def _python_component(name: str) -> dict[str, Any]:
    version = _installed_version(name)
    license_value = _python_license(name)
    return {
        "bom-ref": f"pkg:pypi/{name}@{version}",
        "licenses": [_license_entry(license_value)],
        "name": name,
        "purl": f"pkg:pypi/{name}@{version}",
        "supplier": {"name": "Python Package Index"},
        "type": "library",
        "version": version,
    }


def _installed_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return UNKNOWN_VERSION


def _python_license(name: str) -> str:
    try:
        dist = metadata.metadata(name)
    except metadata.PackageNotFoundError:
        return "NOASSERTION"
    raw_values = [dist.get("License", "")]
    raw_values.extend(dist.get_all("Classifier") or [])
    joined = " ".join(value for value in raw_values if value).lower()
    if "apache" in joined:
        return "Apache-2.0"
    if "mit" in joined:
        return "MIT"
    if "bsd" in joined:
        return "BSD-3-Clause"
    if "mozilla public license" in joined or "mpl" in joined:
        return "MPL-2.0"
    if "isc" in joined:
        return "ISC"
    return "NOASSERTION"


def _collect_node_components(root: Path) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for path in sorted(root.rglob("package-lock.json")):
        if "node_modules" in path.parts:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        packages = payload.get("packages", {})
        if not isinstance(packages, dict):
            continue
        for package_path, details in packages.items():
            if not isinstance(details, dict) or not package_path.startswith("node_modules/"):
                continue
            name = package_path.removeprefix("node_modules/")
            version = str(details.get("version") or UNKNOWN_VERSION)
            license_value = str(details.get("license") or "NOASSERTION")
            components.append(
                {
                    "bom-ref": f"pkg:npm/{name}@{version}",
                    "licenses": [_license_entry(license_value)],
                    "name": name,
                    "purl": f"pkg:npm/{name}@{version}",
                    "supplier": {"name": "npm Registry"},
                    "type": "library",
                    "version": version,
                }
            )
    return components


def _license_entry(value: str) -> dict[str, dict[str, str]]:
    known_spdx = {
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "MIT",
        "MPL-2.0",
    }
    if value in known_spdx:
        return {"license": {"id": value}}
    return {"license": {"name": value or "NOASSERTION"}}


def _dedupe_components(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for component in components:
        key = str(component["purl"])
        deduped[key] = component
    return list(deduped.values())


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)

