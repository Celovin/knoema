# Discord and Slack Bots

Knoema ships optional chat bot entry points for lightweight scenario demos in community or studio channels.

## Install

```powershell
python -m pip install "knoema-engine[bots]"
```

## Discord

Create a Discord application, add a bot user, and invite it with message-send permissions. Then run:

```powershell
$env:DISCORD_BOT_TOKEN="..."
knoema-discord-bot
```

Command:

```text
!knoema run "Dorm: two agents" --ticks 4
```

The bot replies with an embed containing the scenario, tick count, agent count, and action mix.

## Slack

Create a Slack app with Socket Mode enabled and a slash command named `/knoema`. Then run:

```powershell
$env:SLACK_BOT_TOKEN="xoxb-..."
$env:SLACK_APP_TOKEN="xapp-..."
knoema-slack-bot
```

Command:

```text
/knoema run "Village: ten agents" --ticks 4
```

The bot replies with Block Kit blocks containing the same summary fields as Discord.

## Local Scripts

The console scripts call these source entry points:

```powershell
python scripts\run_discord_bot.py
python scripts\run_slack_bot.py
```

Both bots use a deterministic local simulation for channel-safe demos. API provider keys are not required.
