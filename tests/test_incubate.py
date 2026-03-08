from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nexusforge.capture import capture_idea_message
from nexusforge.config import Config
from nexusforge.incubate import incubate_ideas
from nexusforge.storage import load_idea


def make_config(root: Path) -> Config:
    return Config(
        vault_root=root,
        ideas_dir=root / "ideas",
        incubations_dir=root / "incubations",
        taskboard_outbox_dir=root / "taskboard-outbox",
        logs_dir=root / "logs",
    )


class IncubateTests(unittest.TestCase):
    def test_incubation_updates_status_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = make_config(Path(temp_dir))
            idea, path = capture_idea_message("idea: AI自动debug代码", config, source="demo")
            result = incubate_ideas(config, slug=idea.slug, create_task=True)
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0].report_path.exists())
            reloaded = load_idea(Path(path))
            self.assertEqual(reloaded.status, "Incubating")
            self.assertIsNotNone(reloaded.incubation_report)
            self.assertIsNotNone(reloaded.task_card_id)
            outbox_path = config.taskboard_outbox_dir / f"{idea.slug}.json"
            self.assertTrue(outbox_path.exists())


if __name__ == "__main__":
    unittest.main()

