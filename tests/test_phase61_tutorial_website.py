from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

NPM = "npm.cmd" if os.name == "nt" else "npm"


def test_phase61_tutorial_files_exist() -> None:
    expected = [
        "website/app/tutorial/page.tsx",
        "website/app/tutorial/TutorialClient.tsx",
        "website/app/tutorial/tutorial.module.css",
        "website/e2e/tutorial.spec.ts",
        "website/scripts/performance-budget.mjs",
        "docs/website/tutorial.md",
    ]

    for path in expected:
        assert Path(path).exists()


def test_phase61_tutorial_has_five_required_chapters_and_surfaces() -> None:
    source = Path("website/app/tutorial/TutorialClient.tsx").read_text(encoding="utf-8")

    for title in [
        "Your First Agent",
        "Memory & Relationships",
        "Scenario DSL",
        "Theory of Mind",
        "Deploy to Production",
    ]:
        assert title in source

    assert source.count("title:") >= 5
    assert "data-monaco-editor=\"true\"" in source
    assert "window.localStorage.setItem" in source
    assert "Run" in source
    assert "Complete chapter" in source


def test_phase61_package_declares_build_e2e_and_performance_scripts() -> None:
    package = json.loads(Path("website/package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build"] == "next build"
    assert package["scripts"]["e2e"] == "playwright test"
    assert package["scripts"]["perf"] == "node scripts/performance-budget.mjs"


def test_phase61_performance_budget_script_passes() -> None:
    result = subprocess.run(
        [NPM, "--prefix", "website", "run", "perf"],
        check=True,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout[result.stdout.index("{") :])

    assert payload["score"] >= 90
    assert all(payload["checks"].values())


def test_phase61_playwright_docs_and_navigation_are_linked() -> None:
    e2e = Path("website/e2e/tutorial.spec.ts").read_text(encoding="utf-8")
    docs = Path("docs/website/tutorial.md").read_text(encoding="utf-8")

    assert e2e.count("test(") >= 2
    assert "/tutorial" in e2e
    assert "npm --prefix website run e2e" in docs
    assert "Interactive Tutorial Website: website/tutorial.md" in Path("mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "Phase 61 interactive 5-chapter tutorial website" in Path("CHANGELOG.md").read_text(
        encoding="utf-8"
    )
