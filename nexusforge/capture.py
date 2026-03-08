from __future__ import annotations

import re

from nexusforge.config import Config
from nexusforge.models import IdeaRecord
from nexusforge.storage import ensure_unique_slug, save_idea, slugify
from nexusforge.timeutil import current_timestamp


TAG_RULES: list[tuple[tuple[str, ...], str]] = [
    (("ai", "agent", "llm", "模型", "自动"), "AI工具"),
    (("debug", "代码", "bug", "开发", "api", "工程"), "开发效率"),
    (("obsidian", "notion", "知识", "vault", "笔记"), "知识管理"),
    (("提醒", "习惯", "节奏", "todo", "任务"), "效率系统"),
    (("生活", "家务", "健身", "饮食"), "生活hack"),
    (("nexus", "router", "rhythm", "forge"), "Nexus生态"),
]


def capture_idea_message(
    message: str,
    config: Config,
    source: str = "manual",
    title: str | None = None,
    tags: list[str] | None = None,
) -> tuple[IdeaRecord, str]:
    config.ensure_directories()
    description = extract_idea_body(message, config.capture_prefixes)
    final_title = title or suggest_title(description)
    base_slug = slugify(final_title)
    slug = ensure_unique_slug(config.ideas_dir, base_slug)
    now = current_timestamp(config.vault_timezone)
    idea = IdeaRecord(
        title=final_title,
        slug=slug,
        description=description,
        tags=tags or suggest_tags(description),
        status="New",
        created_at=now,
        updated_at=now,
        source=source,
    )
    path = save_idea(config.ideas_dir, idea)
    confirmation = f"Idea captured! Stored as {idea.title}."
    return idea, str(path)


def extract_idea_body(message: str, prefixes: tuple[str, ...]) -> str:
    content = message.strip()
    for prefix in prefixes:
        if content.lower().startswith(prefix.lower()):
            trimmed = content[len(prefix) :].strip()
            if trimmed:
                return trimmed
            break
    raise ValueError(
        f"Message does not start with a supported prefix: {', '.join(prefixes)}"
    )


def suggest_title(description: str) -> str:
    fragments = re.split(r"[。.!?\n]+", description)
    primary = next((item.strip() for item in fragments if item.strip()), description.strip())
    if " " in primary:
        words = primary.split()
        primary = " ".join(words[:6])
    primary = primary.strip(" -_:")
    if len(primary) > 24:
        primary = primary[:24].rstrip(" -_:")
    return primary or "Untitled Idea"


def suggest_tags(description: str) -> list[str]:
    lowered = description.lower()
    tags: list[str] = []
    for keywords, tag in TAG_RULES:
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    if not tags:
        tags.append("未分类")
    return dedupe(tags)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
