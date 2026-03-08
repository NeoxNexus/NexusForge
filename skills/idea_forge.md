# Idea Forge Skill

## Goal

Turn a stored `New` idea into an incubation report with restatement, problem framing, feasibility, milestones, dependencies, action items and SCAMPER variants.

## Steps

1. Find a target idea slug with:

```bash
python3 -m nexusforge.cli list --status New
```

2. Run the forge flow:

```bash
python3 -m nexusforge.cli incubate --slug "<idea-slug>" --create-task
```

3. Confirm:

- The idea status changed from `New` to `Incubating`.
- A report exists under `/Users/neo/ideas-vault/incubations`.
- A task card exists remotely or in `/Users/neo/ideas-vault/taskboard-outbox`.

## Output contract

- Keep the plan actionable and local-first.
- If an external integration is missing, use the outbox fallback instead of failing hard.

