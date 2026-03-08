# Capture Skill

## Goal

Capture messages that start with `新点子：`, `新点子:`, `idea:` or `idea：` and persist them into the local Obsidian-compatible vault.

## Trigger

- User sends a short idea through OpenClaw, Telegram or Discord.
- The message begins with a supported capture prefix.

## Steps

1. Validate that the input starts with a supported prefix.
2. Run:

```bash
python3 -m nexusforge.cli capture "<original message>" --source openclaw
```

3. Return the confirmation:

```text
Idea captured! Stored as <title>.
```

4. If capture fails because the prefix is missing, ask the user to resend with `新点子：` or `idea:`.

