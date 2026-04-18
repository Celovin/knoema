# Discord Community Launch Kit

This document is a launch kit for creating the public Knoema Engine Discord community. It is safe to publish with the repository and contains no account credentials, invite tokens, or private planning notes.

## Server Basics

- Server name: Knoema Engine
- Purpose: persistent-agent simulation discussion for builders, researchers, and game AI developers
- Public link target: GitHub repository, docs, examples, and dashboard demos
- Tone: practical, research-aware, synthetic-data-first

## Roles

| Role | Purpose |
| --- | --- |
| Maintainer | Repository maintainers and release operators |
| Contributor | People submitting issues, docs, examples, or code |
| Researcher | Academic or applied simulation researchers |
| Game Builder | Developers testing NPC and engine adapter workflows |
| Observer | Read-first community members |

## Channel Layout

| Channel | Use |
| --- | --- |
| `#start-here` | Rules, repository links, and onboarding |
| `#announcements` | Releases, notebook updates, dashboard changes |
| `#demo-gallery` | Screenshots, JSONL replays, dashboard captures |
| `#research-notes` | Synthetic social simulation and evaluation notes |
| `#game-npc-lab` | Godot adapter, NPC memory, dialogue experiments |
| `#help` | Install, CLI, notebook, and dashboard support |
| `#dev-log` | Maintainer updates and near-term work |

Optional private channels:

| Channel | Use |
| --- | --- |
| `#maintainers` | Release coordination and moderation decisions |
| `#triage` | Incoming bug reports before public response |

## Server Rules

1. Use only fictional, synthetic, or fully consented data.
2. Do not post real incident names, victim names, suspect names, addresses, operational logs, or sensitive case details.
3. Do not frame Knoema as a prediction, surveillance, profiling, or suspect-scoring system.
4. Do not paste API keys, access tokens, private repository links, or credentials.
5. Keep research criticism concrete and evidence-based.
6. Keep demos reproducible: include config, commit hash, or notebook path when possible.
7. Respect maintainers' safety calls on public-safety, privacy, and data-use boundaries.

## Pinned Links

- Repository: `https://github.com/Celovin/knoema`
- README: `README.md`
- Korean README: `README.ko.md`
- CLI docs: `docs/cli.md`
- Prompt docs: `docs/prompts.md`
- Dashboard docs: `dashboard/README.md`
- Tutorial draft: `docs/tutorial_blog.md`
- Research positioning: `docs/research.md`

## First Announcement Draft

Knoema Engine is an early MVP for persistent-agent simulation. The first public surface includes a Python package, deterministic CLI runs, executable notebooks, a Streamlit replay dashboard, multilingual prompt templates, semantic-temporal memory retrieval, and a Godot adapter scaffold.

The community starts with one rule: keep examples synthetic and reproducible. Share configs, notebooks, dashboard captures, and engine adapter experiments. Avoid real-world sensitive data.

Start here:

- Run `knoema run examples/cli_dorm.yaml --json`
- Open the dashboard with `streamlit run dashboard/app.py`
- Read `docs/tutorial_blog.md`
- Share questions in `#help` and demos in `#demo-gallery`

## Launch Checklist

1. Create the Discord server with the name `Knoema Engine`.
2. Add roles from the role table.
3. Create public channels from the channel layout.
4. Create private maintainer channels only if needed.
5. Paste server rules into `#start-here`.
6. Pin the links from the pinned links section.
7. Post the first announcement.
8. Generate a non-expiring invite only after rules and moderation settings are configured.
9. Add the invite link to README after the repository is public and the server is ready.

## Moderation Checklist

- Remove real personal data immediately.
- Ask users to replace sensitive examples with synthetic equivalents.
- Move bug reports with reproducible steps to GitHub Issues.
- Keep roadmap discussion in `#dev-log` unless it needs issue tracking.
- Revoke public invite links if spam starts before moderation is stable.
