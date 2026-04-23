from __future__ import annotations

import json
from pathlib import Path


def test_phase25_website_files_exist() -> None:
    expected = [
        "website/package.json",
        "website/next.config.mjs",
        "website/tsconfig.json",
        "website/app/layout.tsx",
        "website/app/page.tsx",
        "website/app/globals.css",
        "website/app/icon.svg",
        "website/app/docs/page.tsx",
        "website/app/research/page.tsx",
        "website/app/showcase/page.tsx",
        "website/app/blog/page.tsx",
        "website/components/LuvoireLanding.tsx",
        "website/components/heroGrid.ts",
        "website/public/og-image.png",
        "website/public/figures/memory_recall.svg",
        "website/public/figures/token_efficiency.svg",
        "website/public/figures/branching.svg",
        "website/public/figures/scalability.svg",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase25_website_package_scripts_are_buildable() -> None:
    package = json.loads(Path("website/package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build"] == "next build"
    assert package["dependencies"]["next"] == "16.2.4"
    assert package["dependencies"]["react"] == "19.2.5"


def test_phase25_website_copy_keeps_safety_and_sdk_surfaces() -> None:
    page = Path("website/app/page.tsx").read_text(encoding="utf-8")
    landing = Path("website/components/LuvoireLanding.tsx").read_text(encoding="utf-8")
    hero_grid = Path("website/components/heroGrid.ts").read_text(encoding="utf-8")
    docs = Path("website/app/docs/page.tsx").read_text(encoding="utf-8")
    showcase = Path("website/app/showcase/page.tsx").read_text(encoding="utf-8")

    combined = "\n".join([page, landing, hero_grid, docs, showcase])

    assert "LuvoireLanding" in page
    assert "City-scale multi-agent simulation with deterministic replay" in combined
    assert "pip install luvoire-engine" in combined
    assert "Python" in combined
    assert "TypeScript" in combined
    assert "Godot" in combined
    assert "CC-BY-4.0 dataset" in combined
    assert "Audit log, PIPA-ready" in combined


def test_phase25_website_has_seo_canvas_and_image_loading_basics() -> None:
    layout = Path("website/app/layout.tsx").read_text(encoding="utf-8")
    landing = Path("website/components/LuvoireLanding.tsx").read_text(encoding="utf-8")
    hero_grid = Path("website/components/heroGrid.ts").read_text(encoding="utf-8")
    research = Path("website/app/research/page.tsx").read_text(encoding="utf-8")
    docs = Path("website/app/docs/page.tsx").read_text(encoding="utf-8")
    showcase = Path("website/app/showcase/page.tsx").read_text(encoding="utf-8")
    blog = Path("website/app/blog/page.tsx").read_text(encoding="utf-8")

    assert "alternates" in layout
    assert "robots" in layout
    assert "twitter" in layout
    assert 'images: ["/og-image.png"]' in layout
    assert 'aria-label="Deterministic replay preview"' in landing
    assert 'className="grid-canvas"' in landing
    assert "requestAnimationFrame" in hero_grid
    assert 'loading="lazy"' in research
    assert 'width="960"' in research

    for page in [docs, research, showcase, blog]:
        assert "export const metadata" in page
        assert "canonical" in page
