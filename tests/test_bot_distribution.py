from __future__ import annotations

import tomllib
from pathlib import Path


def test_batch_nn_bot_distribution_files_and_docs() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    docs = Path("docs/bots/setup.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "src/knoema_bots" in pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    assert "discord.py>=2.4" in pyproject["project"]["optional-dependencies"]["bots"]
    assert pyproject["project"]["scripts"]["knoema-discord-bot"] == "knoema_bots.discord:main"
    assert pyproject["project"]["scripts"]["knoema-slack-bot"] == "knoema_bots.slack:main"
    assert "SLACK_BOT_TOKEN" in docs
    assert "DISCORD_BOT_TOKEN" in docs
    assert "bots/setup.md" in mkdocs
