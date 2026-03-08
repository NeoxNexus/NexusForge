from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IdeaRecord:
    title: str
    slug: str
    description: str
    tags: list[str]
    status: str
    created_at: str
    updated_at: str
    source: str = "manual"
    incubation_report: str | None = None
    task_card_id: str | None = None
    path: Path | None = field(default=None, repr=False)

    def to_front_matter(self) -> dict[str, object]:
        return {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "tags": self.tags,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "incubation_report": self.incubation_report,
            "task_card_id": self.task_card_id,
        }

