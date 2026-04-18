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
        "website/components/Hero.tsx",
        "website/components/ThreeApplications.tsx",
        "website/components/CodeDemo.tsx",
        "website/components/Architecture.tsx",
        "website/components/CTA.tsx",
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
    hero = Path("website/components/Hero.tsx").read_text(encoding="utf-8")
    applications = Path("website/components/ThreeApplications.tsx").read_text(encoding="utf-8")
    code_demo = Path("website/components/CodeDemo.tsx").read_text(encoding="utf-8")

    combined = "\n".join([page, hero, applications, code_demo])

    assert "One engine. Three worlds." in combined
    assert "synthetic, non-identifying scenarios" in combined
    assert "from knoema.game import GameSession" in combined
    assert "Python, TypeScript, and GDScript" in combined


def test_phase25_website_has_seo_and_image_loading_basics() -> None:
    layout = Path("website/app/layout.tsx").read_text(encoding="utf-8")
    hero = Path("website/components/Hero.tsx").read_text(encoding="utf-8")
    research = Path("website/app/research/page.tsx").read_text(encoding="utf-8")
    docs = Path("website/app/docs/page.tsx").read_text(encoding="utf-8")
    showcase = Path("website/app/showcase/page.tsx").read_text(encoding="utf-8")
    blog = Path("website/app/blog/page.tsx").read_text(encoding="utf-8")

    assert "alternates" in layout
    assert "robots" in layout
    assert "twitter" in layout
    assert 'src="/og-image.png"' in hero
    assert "priority" in hero
    assert 'className="hero-bg"' in hero
    assert 'loading="lazy"' in research
    assert 'width="960"' in research

    for page in [docs, research, showcase, blog]:
        assert "export const metadata" in page
        assert "canonical" in page
