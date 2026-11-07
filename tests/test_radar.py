import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from radar.core import identity, score
from radar.__main__ import run


class RadarTests(unittest.TestCase):
    def test_tracking_dedup(self):
        self.assertEqual(identity({"url": "https://example.com/job?utm_source=a"}),
                         identity({"url": "https://example.com/job#top"}))
        self.assertNotEqual(identity({"url": "https://example.com/job?id=1"}),
                            identity({"url": "https://example.com/job?id=2"}))

    def test_score_once_per_category(self):
        rules = {"categories": [{"name": "test", "weight": 20, "terms": ["rubric", "benchmark"]}]}
        self.assertEqual(score({"title": "rubric benchmark", "description": ""}, rules)[0], 20)
        self.assertEqual(score({"title": "rubricsomething", "description": ""}, rules)[0], 0)

    def test_delivery_state(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "sent.json"
            config = [{"id": "demo", "enabled": True, "method": "local_json", "path": "examples/jobs.json"}]
            rules = json.loads(Path("config/matching.json").read_text(encoding="utf-8"))
            with patch("radar.__main__.send", side_effect=RuntimeError):
                with self.assertRaises(RuntimeError):
                    run(config, rules, state, True)
            self.assertFalse(state.exists())
            with patch("radar.__main__.send") as sender:
                run(config, rules, state, True)
                self.assertIn("本卡 1 个相关项目", sender.call_args.args[0]["card"]["elements"][0]["text"]["content"])
                run(config, rules, state, True)
                self.assertIn("本卡 0 个相关项目", sender.call_args.args[0]["card"]["elements"][0]["text"]["content"])

    def test_collector_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run([{"id": "bad", "enabled": True, "method": "pending_review"}],
                         {"threshold": 20}, Path(folder) / "state.json")
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()

