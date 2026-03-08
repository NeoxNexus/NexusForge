from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nexusforge.capture import capture_idea_message
from nexusforge.config import Config
from nexusforge.storage import load_idea


def make_config(root: Path) -> Config:
    return Config(
        vault_root=root,
        ideas_dir=root / "ideas",
        incubations_dir=root / "incubations",
        taskboard_outbox_dir=root / "taskboard-outbox",
        logs_dir=root / "logs",
    )


class CaptureTests(unittest.TestCase):
    def test_capture_creates_markdown_idea(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = make_config(Path(temp_dir))
            idea, path = capture_idea_message("新点子：AI自动debug代码", config, source="telegram")
            self.assertTrue(Path(path).exists())
            self.assertEqual(idea.status, "New")
            loaded = load_idea(Path(path))
            self.assertEqual(loaded.description, "AI自动debug代码")
            self.assertIn("AI工具", loaded.tags)
            self.assertIn("开发效率", loaded.tags)

    def test_capture_requires_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = make_config(Path(temp_dir))
            with self.assertRaises(ValueError):
                capture_idea_message("这是一个没有前缀的想法", config)


if __name__ == "__main__":
    unittest.main()

