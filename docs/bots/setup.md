# Discord and Slack Bots

Luvoire ships optional chat bot entry points for lightweight scenario demos in community or studio channels.

## Install

```powershell
python -m pip install "luvoire-engine[bots]"
```

## Discord

Create a Discord application, add a bot user, and invite it with message-send permissions. Then run:

```powershell
$env:DISCORD_BOT_TOKEN="..."
luvoire-discord-bot
```

Command:

```text
!luvoire run "Dorm: two agents" --ticks 4
```

The bot replies with an embed containing the scenario, tick count, agent count, and action mix.

## Slack

Create a Slack app with Socket Mode enabled and a slash command named `/luvoire`. Then run:

```powershell
$env:SLACK_BOT_TOKEN="xoxb-..."
$env:SLACK_APP_TOKEN="xapp-..."
luvoire-slack-bot
```

Command:

```text
/luvoire run "Village: ten agents" --ticks 4
```

The bot replies with Block Kit blocks containing the same summary fields as Discord.

## Local Scripts

The console scripts call these source entry points:

```powershell
python scripts\run_discord_bot.py
python scripts\run_slack_bot.py
```

Both bots use a deterministic local simulation for channel-safe demos. API provider keys are not required.
