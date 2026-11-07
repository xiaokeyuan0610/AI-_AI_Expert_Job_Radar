import json
import unittest
from radar.cards import card_message


class CardTests(unittest.TestCase):
    def test_summary_fields_and_safe_content(self):
        job = {"title": "建筑 <at id=all>", "description": "设计空间。", "url": "https://example.com/job",
               "salary": "100元/小时", "platform_name": "平台甲"}
        payload = card_message([job, job], test=True)
        self.assertEqual(payload["msg_type"], "interactive")
        elements = payload["card"]["elements"]
        self.assertEqual(sum(element["tag"] == "hr" for element in elements), 1)
        self.assertEqual(len(next(element["fields"] for element in elements if "fields" in element)), 2)
        self.assertNotIn("<at id=all>", json.dumps(payload, ensure_ascii=False))
        self.assertIn("AI分析 0/2", elements[-1]["elements"][0]["content"])

    def test_long_analysis_stays_below_delivery_limit(self):
        job = {"title": "室内设计", "url": "https://example.com/job", "analysis": {
            key: "长" * 600 for key in ("summary", "fit_reason", "requirements", "ai_steps", "risks")}}
        job["analysis"].update(fit_score=80, ai_permission="unknown")
        payload = card_message([job] * 3)
        self.assertLess(len(json.dumps(payload, ensure_ascii=False).encode()), 17500)
