from __future__ import annotations

from pathlib import Path

from nexusforge.config import Config
from nexusforge.storage import list_ideas
from nexusforge.timeutil import current_timestamp


def build_heartbeat_summary(config: Config, limit: int = 10) -> str:
    config.ensure_directories()
    pending = [idea for idea in list_ideas(config.ideas_dir) if idea.status == "New"]
    lines = [f"[{current_timestamp(config.vault_timezone)}] NexusForge heartbeat"]
    lines.append(f"Pending ideas: {len(pending)}")
    for idea in pending[:limit]:
        lines.append(f"- {idea.title} [{', '.join(idea.tags)}] ({idea.created_at})")
    if not pending:
        lines.append("- No pending ideas.")
    return "\n".join(lines)


def append_heartbeat_log(config: Config, summary: str) -> Path:
    config.ensure_directories()
    path = config.logs_dir / "heartbeat.log"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(summary)
        handle.write("\n\n")
    return path
