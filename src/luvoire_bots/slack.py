"""Slack bot entry point for Luvoire."""

from __future__ import annotations

import argparse
import importlib
import os
from collections.abc import Mapping, Sequence
from typing import Any

from luvoire_bots.core import format_slack_blocks, parse_bot_command, run_scenario_for_bot


def build_blocks_for_command(command_text: str) -> list[dict[str, Any]]:
    command = parse_bot_command(command_text)
    summary = run_scenario_for_bot(command.scenario, ticks=command.ticks)
    return format_slack_blocks(summary)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Luvoire Slack bot.")
    parser.add_argument("--bot-token", default=os.environ.get("SLACK_BOT_TOKEN", ""))
    parser.add_argument("--app-token", default=os.environ.get("SLACK_APP_TOKEN", ""))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.bot_token or not args.app_token:
        raise RuntimeError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN are required")

    slack_bolt = importlib.import_module("slack_bolt")
    socket_mode = importlib.import_module("slack_bolt.adapter.socket_mode")
    app = slack_bolt.App(token=args.bot_token)

    @app.command("/luvoire")  # type: ignore[untyped-decorator]
    def luvoire_command(ack: Any, respond: Any, command: Mapping[str, Any]) -> None:
        ack()
        text = str(command.get("text", "")).strip()
        respond(blocks=build_blocks_for_command(f"luvoire {text}"))

    socket_mode.SocketModeHandler(app, args.app_token).start()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
