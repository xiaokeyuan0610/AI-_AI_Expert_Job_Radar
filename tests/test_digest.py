import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from radar.__main__ import run
from radar.core import message


class DigestTests(unittest.TestCase):
    def test_grouped_summary(self):
        payload = message([{"title": "视频评测", "description": "评审视频生成质量。其他内容。",
                            "url": "https://example.com/job", "platform_name": "平台甲"}], [])
        text = payload["content"]["text"]
        self.assertIn("【平台甲】", text)
        self.assertIn("做什么：评审视频生成质量", text)
        self.assertNotIn("其他内容", text)

    @patch("radar.__main__.send")
    @patch("radar.__main__.collect")
    def test_no_five_job_cap(self, collect, send):
        collect.return_value = [{"title": "视频", "description": "评测", "url": f"https://example.com/{index}"}
                                for index in range(12)]
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "sent.json"
            run([{"id": "one", "enabled": True}],
                {"threshold": 0, "categories": [], "batch_size": 10}, state, True)
            self.assertEqual(len(json.loads(state.read_text())), 12)
            self.assertEqual(send.call_count, 2)
