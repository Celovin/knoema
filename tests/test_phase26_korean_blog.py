from __future__ import annotations

from pathlib import Path

POSTS = [
    "01-why-luvoire-korean-indie-games.md",
    "02-llm-npc-memory-principles.md",
    "03-godot-integration-step-by-step.md",
    "04-academic-research-reproducibility.md",
    "05-crime-simulation-ethics-and-guards.md",
]


def test_phase26_korean_blog_posts_and_thumbnails_exist() -> None:
    expected = [f"docs/blog/ko/{name}" for name in POSTS]
    expected.extend(
        [
            f"docs/blog/ko/thumbnails/{name.replace('.md', '.svg')}"
            for name in POSTS
        ]
    )

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase26_posts_include_public_links_and_safety_language() -> None:
    for name in POSTS:
        content = Path("docs/blog/ko", name).read_text(encoding="utf-8")

        assert "https://github.com/Celovin/luvoire" in content
        assert "https://huggingface.co/spaces/celovin/luvoire-playground" in content or name in {
            "03-godot-integration-step-by-step.md",
            "04-academic-research-reproducibility.md",
            "05-crime-simulation-ethics-and-guards.md",
        }

    safety = Path("docs/blog/ko/05-crime-simulation-ethics-and-guards.md").read_text(
        encoding="utf-8"
    )
    assert "실제 사람을 평가하지 않는다" in safety
    assert "미래를 단정하지 않는다" in safety
