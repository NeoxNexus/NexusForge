from __future__ import annotations

import json
import re
from pathlib import Path

from nexusforge.models import IdeaRecord


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", value.strip().lower(), flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-_")
    return slug[:48] or "idea"


def ensure_unique_slug(directory: Path, slug: str) -> str:
    candidate = slug
    counter = 2
    while (directory / f"{candidate}.md").exists():
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


def dump_front_matter(data: dict[str, object]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
            continue
        if value is None:
            lines.append(f"{key}: null")
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def split_front_matter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    metadata_lines: list[str] = []
    body_start = 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            body_start = index + 1
            break
        metadata_lines.append(lines[index])
    metadata = parse_front_matter_lines(metadata_lines)
    body = "\n".join(lines[body_start:]).lstrip("\n")
    return metadata, body


def parse_front_matter_lines(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == "":
            items: list[object] = []
            index += 1
            while index < len(lines) and lines[index].startswith("  - "):
                items.append(parse_scalar(lines[index][4:].strip()))
                index += 1
            data[key] = items
            continue
        data[key] = parse_scalar(raw_value)
        index += 1
    return data


def parse_scalar(raw: str) -> object:
    if raw == "null":
        return None
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    return raw


def idea_to_markdown(idea: IdeaRecord) -> str:
    front_matter = dump_front_matter(idea.to_front_matter())
    body = "\n".join(
        [
            f"# {idea.title}",
            "",
            idea.description.strip(),
            "",
            "## Metadata",
            "",
            f"- Status: {idea.status}",
            f"- Tags: {', '.join(idea.tags)}",
            f"- Source: {idea.source}",
        ]
    ).strip()
    return f"{front_matter}\n\n{body}\n"


def save_idea(directory: Path, idea: IdeaRecord) -> Path:
    path = directory / f"{idea.slug}.md"
    path.write_text(idea_to_markdown(idea), encoding="utf-8")
    idea.path = path
    return path


def load_idea(path: Path) -> IdeaRecord:
    text = path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(text)
    description = str(metadata.get("description") or extract_description_from_body(body))
    tags = [str(item) for item in metadata.get("tags", [])]
    return IdeaRecord(
        title=str(metadata.get("title", path.stem)),
        slug=str(metadata.get("slug", path.stem)),
        description=description,
        tags=tags,
        status=str(metadata.get("status", "New")),
        created_at=str(metadata.get("created_at", "")),
        updated_at=str(metadata.get("updated_at", metadata.get("created_at", ""))),
        source=str(metadata.get("source", "manual")),
        incubation_report=_optional_str(metadata.get("incubation_report")),
        task_card_id=_optional_str(metadata.get("task_card_id")),
        path=path,
    )


def extract_description_from_body(body: str) -> str:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    for line in lines:
        if not line.startswith("#") and not line.startswith("- Status:"):
            return line
    return ""


def list_ideas(directory: Path) -> list[IdeaRecord]:
    ideas = [load_idea(path) for path in sorted(directory.glob("*.md"))]
    return sorted(ideas, key=lambda item: item.created_at, reverse=True)


def write_markdown(path: Path, front_matter: dict[str, object], body: str) -> Path:
    payload = f"{dump_front_matter(front_matter)}\n\n{body.strip()}\n"
    path.write_text(payload, encoding="utf-8")
    return path


def _optional_str(value: object) -> str | None:
    if value in (None, "", "null"):
        return None
    return str(value)
