# NexusForge

NexusForge is a local-first MVP for capturing ideas, storing them in an Obsidian-compatible vault, incubating them into executable plans, and optionally pushing derived tasks to a task board.

## What is included

- `python3 -m nexusforge.cli capture`: capture ideas from prefixed messages such as `新点子：...` or `idea: ...`
- `python3 -m nexusforge.cli serve`: expose local webhook endpoints for Telegram/Discord-style payloads
- `python3 -m nexusforge.cli incubate`: scan `New` ideas and generate incubation reports
- `python3 -m nexusforge.cli heartbeat`: summarize pending ideas
- `python3 -m nexusforge.cli install-heartbeat`: install a daily cron job using `CRON_TZ=America/Los_Angeles`
- `python3 -m nexusforge.cli demo`: run an end-to-end local demo

## Vault layout

By default, NexusForge uses:

- `/Users/neo/ideas-vault/ideas`
- `/Users/neo/ideas-vault/incubations`
- `/Users/neo/ideas-vault/taskboard-outbox`
- `/Users/neo/ideas-vault/logs`

The markdown files use YAML front matter compatible with Obsidian and Dataview.

## Quick start

```bash
python3 -m nexusforge.cli init
python3 -m nexusforge.cli capture "新点子：AI自动debug代码"
python3 -m nexusforge.cli list --status New
python3 -m nexusforge.cli incubate --top 1 --create-task
python3 -m nexusforge.cli heartbeat
```

## Webhook endpoints

Run:

```bash
python3 -m nexusforge.cli serve --port 8765
```

Then send JSON:

- `POST /capture` with `{"text": "idea: ..."}`
- `POST /telegram` with Telegram update payloads containing `message.text`
- `POST /discord` with Discord-style payloads containing `content`

## Configuration

Optional repo config file:

- `/Users/neo/workspace/NexusForge/config/nexusforge.toml`

The default config is safe to run locally. If `taskboard.endpoint` is not configured, generated task cards are written to the outbox directory instead of making network calls.

## Skills

OpenClaw-oriented skill prompts are available under:

- `/Users/neo/workspace/NexusForge/skills/capture.md`
- `/Users/neo/workspace/NexusForge/skills/idea_forge.md`
- `/Users/neo/workspace/NexusForge/skills/incubate.md`

