from __future__ import annotations

from pathlib import Path


def test_phase14_discord_community_launch_kit_is_publishable() -> None:
    text = Path("docs/discord_community.md").read_text(encoding="utf-8")

    required_sections = [
        "# Discord Community Launch Kit",
        "## Server Rules",
        "## First Announcement Draft",
        "## Launch Checklist",
        "## Moderation Checklist",
    ]

    assert all(section in text for section in required_sections)
    assert "#help" in text
    assert "#demo-gallery" in text
    assert "Do not paste API keys" in text
    assert "TODO" not in text
