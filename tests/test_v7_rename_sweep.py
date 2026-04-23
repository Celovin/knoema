from __future__ import annotations

import subprocess
from pathlib import Path

TOKEN_ARGS = ["knoema", "Knoema", "KNOEMA"]

MIGRATION_DOCS = {
    Path("docs/migration/legacy-name.md"),
}

ALLOWLIST = {
    Path("src/knoema/__init__.py"),
    Path("src/knoema_compat/__init__.py"),
    Path("tests/test_knoema_compat_shim.py"),
    Path("tests/test_v7_rename_sweep.py"),
    # Slot B backward-compat env var references (KNOEMA_* string literals accepted
    # for one release cycle per v7 handoff §2.2 env var compatibility shim).
    Path("src/luvoire/api/auth.py"),
    Path("src/luvoire/api/rate_limit.py"),
    Path("src/luvoire/api/server.py"),
    Path("src/luvoire/config.py"),
    Path("src/luvoire_mcp/server.py"),
    Path("src/luvoire/multimodal/tts.py"),
    Path("src/luvoire/telemetry/client.py"),
    Path("tests/test_bench_replay_perf.py"),
    Path("tests/test_env_var_compat_shim.py"),
    Path("tests/test_mcp_server.py"),
    Path("tests/test_phase62_release.py"),
}

PRODUCT_SURFACE_PREFIXES = (
    ".github/",
    "adapters/",
    "bench/",
    "benchmarks/",
    "dashboard/",
    "demo/",
    "deploy/",
    "docs/",
    "evaluation/",
    "examples/",
    "extensions/",
    "legal/",
    "playground/",
    "POLICIES/",
    "saas/",
    "scenarios/",
    "scenarios_hub/",
    "schemas/",
    "sdk/",
    "site-snapshot/",
    "unity-sdk/",
    "website/",
)

PRODUCT_SURFACE_FILES = {
    ".dockerignore",
    ".env.local.example",
    ".gitattributes",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".release-please-manifest.json",
    ".zenodo.json",
    "ATTRIBUTIONS.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "docker-compose.yml",
    "Dockerfile",
    "LICENSE",
    "LICENSE-NEMOTRON.md",
    "mkdocs.yml",
    "README.de.md",
    "README.es.md",
    "README.fr.md",
    "README.ja.md",
    "README.ko.md",
    "README.md",
    "README.zh-CN.md",
    "README.zh-TW.md",
    "RELEASE.md",
}

TEXT_SUFFIXES = {
    ".asmdef",
    ".cfg",
    ".cff",
    ".cpp",
    ".cs",
    ".css",
    ".gd",
    ".h",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".kt",
    ".kts",
    ".md",
    ".py",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".uplugin",
    ".yaml",
    ".yml",
}


def test_slot_a_python_sources_have_only_explicit_legacy_compat_tokens() -> None:
    candidates = [
        path
        for path in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
        if path.startswith(("src/", "tests/", "scripts/")) and Path(path).suffix == ".py"
    ]
    offenders: list[str] = []
    for rel in candidates:
        path = Path(rel)
        if path in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in TOKEN_ARGS):
            offenders.append(rel)

    assert offenders == []


def test_product_surfaces_do_not_expose_legacy_brand_tokens() -> None:
    candidates = [
        path
        for path in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
        if _is_product_surface_text_path(Path(path))
    ]
    offenders: list[str] = []
    for rel in candidates:
        path = Path(rel)
        if path in MIGRATION_DOCS:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in TOKEN_ARGS):
            offenders.append(rel)

    assert offenders == []


def _is_product_surface_text_path(path: Path) -> bool:
    rel = path.as_posix()
    if rel == "CHANGELOG.md" or rel.startswith("planning/"):
        return False
    if rel in PRODUCT_SURFACE_FILES:
        return True
    return rel.startswith(PRODUCT_SURFACE_PREFIXES) and path.suffix in TEXT_SUFFIXES
