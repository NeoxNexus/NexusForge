from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from nexusforge.config import Config
from nexusforge.models import IdeaRecord


def create_task_card(
    config: Config,
    idea: IdeaRecord,
    report_path: Path,
    action_items: list[str],
) -> tuple[str, str]:
    payload = {
        "title": idea.title,
        "status": "In Progress",
        "source_idea": idea.slug,
        "source_report": str(report_path),
        "summary": idea.description,
        "tags": idea.tags,
        "action_items": action_items,
        "created_at": idea.updated_at,
    }
    if not config.taskboard_endpoint:
        outbox_path = write_outbox_card(config.taskboard_outbox_dir, idea.slug, payload)
        return f"outbox:{outbox_path.stem}", str(outbox_path)

    request = urllib.request.Request(
        config.taskboard_endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **(
                {"Authorization": f"Bearer {config.taskboard_api_key}"}
                if config.taskboard_api_key
                else {}
            ),
        },
        method="POST",
    )

    last_error = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read().decode("utf-8") or "{}"
                parsed = json.loads(raw)
                card_id = str(parsed.get("id") or parsed.get("card_id") or f"http:{response.status}")
                return card_id, config.taskboard_endpoint
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = str(error)
            if attempt < 2:
                time.sleep(1)

    outbox_path = write_outbox_card(config.taskboard_outbox_dir, idea.slug, payload)
    return f"retry-failed:{last_error}", str(outbox_path)


def write_outbox_card(directory: Path, slug: str, payload: dict[str, object]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slug}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

