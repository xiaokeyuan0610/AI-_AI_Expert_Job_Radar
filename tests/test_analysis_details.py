import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
from radar.ai_analysis import analyze_batch, enrich_jobs, TEXT_FIELDS
from radar.details import deadline_text, deadline_at, pay_text, CHINA
from radar.recommendations import recommendation


class AnalysisDetailsTests(unittest.TestCase):
    def test_time_formats_and_urgency(self):
        now = datetime(2026, 11, 7, 9, tzinfo=CHINA)
        self.assertIn("24小时内", deadline_text({"deadline": "2026-11-08T00:00:00+08:00"}, now))
        self.assertIn("已截止", deadline_text({"deadline": "2026-11-01"}, now))
        self.assertEqual(deadline_text({}), "平台未注明")
        self.assertEqual(deadline_at({"deadline": 1794585600}), deadline_at({"deadline": 1794585600000}))
        self.assertEqual(pay_text({"salary": "100–100元/hour"}), "100元/小时")

    def test_star_differences(self):
        job = {"title": "建筑评测", "description": "", "salary": "100元/题"}
        high = dict(job, analysis={"fit_score": 95, "ai_permission": "unknown"})
        low = dict(job, analysis={"fit_score": 10, "ai_permission": "unknown"})
        self.assertNotEqual(recommendation(high)[:5], recommendation(low)[:5])
        self.assertNotIn("★★★★★", recommendation(high))

    @patch.dict("os.environ", {"OPENAI_API_KEY": ""})
    def test_missing_key_is_explicit(self):
        result = enrich_jobs([{"title": "建筑"}])
        self.assertIn("AI未配置", result[0]["analysis_status"])

    @patch("radar.ai_analysis.urllib.request.build_opener")
    def test_structured_output_and_permission_evidence(self, opener):
        item = {field: "简短分析" for field in TEXT_FIELDS}
        item.update(index=0, fit_score=80, ai_permission="allowed", permission_evidence="不存在的证据")
        response = MagicMock()
        response.read.return_value = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"jobs": [item]})}}]}).encode()
        opener.return_value.open.return_value.__enter__.return_value = response
        result = analyze_batch([{"title": "建筑", "description": "招聘建筑专家"}], {}, "fake-test-key", "gpt-5-mini")
        self.assertEqual(result[0]["analysis"]["ai_permission"], "unknown")
        self.assertEqual(result[0]["analysis_status"], "OpenAI已分析")
        item["index"] = 2
        response.read.return_value = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"jobs": [item]})}}]}).encode()
        with self.assertRaises(ValueError):
            analyze_batch([{"title": "建筑"}], {}, "fake-test-key", "gpt-5-mini")
