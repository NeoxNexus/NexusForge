from __future__ import annotations

import unittest

from nexusforge.webhook import extract_message_text, source_from_path


class WebhookTests(unittest.TestCase):
    def test_extract_telegram_text(self) -> None:
        payload = {"message": {"text": "新点子：测试 webhook 捕捉"}}
        self.assertEqual(extract_message_text(payload, "telegram"), "新点子：测试 webhook 捕捉")

    def test_extract_discord_text(self) -> None:
        payload = {"content": "idea: discord flow"}
        self.assertEqual(extract_message_text(payload, "discord"), "idea: discord flow")

    def test_source_from_path(self) -> None:
        self.assertEqual(source_from_path("/capture"), "capture")
        self.assertEqual(source_from_path("/telegram"), "telegram")
        self.assertEqual(source_from_path("/discord"), "discord")
        self.assertIsNone(source_from_path("/unknown"))


if __name__ == "__main__":
    unittest.main()
