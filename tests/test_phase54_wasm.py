from __future__ import annotations

import json
from pathlib import Path

WASM_ROOT = Path("adapters/wasm")


def test_phase54_wasm_runtime_files_exist() -> None:
    expected = [
        "package.json",
        "scripts/build.mjs",
        "src/knoema-core.ts",
        "index.html",
        "demo/knoema-core.js",
        "demo/2-agent.html",
        "demo/5-agent.html",
        "demo/sally-anne.html",
        "tests/wasm-runtime.test.mjs",
        "tests/e2e.mjs",
    ]

    for relative_path in expected:
        assert (WASM_ROOT / relative_path).exists()


def test_phase54_wasm_package_declares_build_test_and_e2e_scripts() -> None:
    package = json.loads((WASM_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build"] == "node scripts/build.mjs"
    assert "wasm-runtime.test.mjs" in package["scripts"]["test"]
    assert "tests/e2e.mjs" in package["scripts"]["e2e"]


def test_phase54_wasm_bundle_is_under_five_hundred_kb_and_has_runtime_api() -> None:
    bundle = WASM_ROOT / "demo/knoema-core.js"
    text = bundle.read_text(encoding="utf-8")

    assert bundle.stat().st_size < 500_000
    for symbol in [
        "class Persona",
        "class Environment",
        "class LocalClient",
        "function runSimulation",
        "function runSallyAnneDemo",
    ]:
        assert symbol in text


def test_phase54_wasm_demo_is_copied_to_website_static_path() -> None:
    assert Path("website/app/wasm-demo/page.tsx").exists()
    assert Path("website/public/wasm/index.html").exists()
    assert Path("website/public/wasm/demo/knoema-core.js").exists()


def test_phase54_docs_and_navigation_are_linked() -> None:
    assert "Browser WASM Runtime: adapters/wasm.md" in Path("mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "npm --prefix adapters\\wasm run build" in Path("docs/adapters/wasm.md").read_text(
        encoding="utf-8"
    )
