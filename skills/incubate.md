# Incubate Skill

## Goal

Scan the vault for pending ideas and incubate the highest-priority items.

## Steps

1. List pending ideas:

```bash
python3 -m nexusforge.cli list --status New
```

2. Incubate the top three:

```bash
python3 -m nexusforge.cli incubate --top 3 --create-task
```

3. Run a heartbeat summary:

```bash
python3 -m nexusforge.cli heartbeat
```

4. If task board credentials are missing, verify that JSON payloads were written to `/Users/neo/ideas-vault/taskboard-outbox`.

