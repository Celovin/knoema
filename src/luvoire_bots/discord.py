"""Discord bot entry point for Luvoire."""

from __future__ import annotations

import argparse
import importlib
import os
from collections.abc import Sequence
from typing import Any

from luvoire_bots.core import format_discord_embed, parse_bot_command, run_scenario_for_bot


def build_embed_for_command(command_text: str) -> dict[str, Any]:
    command = parse_bot_command(command_text)
    summary = run_scenario_for_bot(command.scenario, ticks=command.ticks)
    return format_discord_embed(summary)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Luvoire Discord bot.")
    parser.add_argument("--token", default=os.environ.get("DISCORD_BOT_TOKEN", ""))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")

    discord_module = importlib.import_module("discord")
    commands_module = importlib.import_module("discord.ext.commands")
    intents = discord_module.Intents.default()
    bot = commands_module.Bot(command_prefix="!", intents=intents)

    @bot.command(name="luvoire")  # type: ignore[untyped-decorator]
    async def luvoire_command(ctx: Any, *parts: str) -> None:
        embed_payload = build_embed_for_command(" ".join(("luvoire", *parts)))
        embed = discord_module.Embed(
            title=embed_payload["title"],
            description=embed_payload["description"],
            color=embed_payload["color"],
        )
        for field in embed_payload["fields"]:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field["inline"],
            )
        await ctx.send(embed=embed)

    bot.run(args.token)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
