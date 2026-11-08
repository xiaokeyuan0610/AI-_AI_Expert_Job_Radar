import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
from radar.ai_analysis import analyze_batch, enrich_jobs, TEXT_FIELDS
from radar.details import deadline_text, deadline_at, pay_text, CHINA
from radar.recommendations import recommendation


class AnalysisDetailsTests(unittest.TestCase):
    @patch.dict("os.environ", {"AI_BASE_URL": "https://api.metarouters.org/v1", "AI_API_KEY": "test", "AI_MODEL": "test"}, clear=True)
    @patch("radar.ai_analysis.load_profile", return_value={})
    @patch("radar.ai_analysis.analyze_batch")
    def test_invalid_batch_does_not_poison_later_jobs(self, analyze, profile):
        jobs = [{"title": str(index)} for index in range(4)]
        analyze.side_effect = [ValueError("invalid"), [dict(jobs[0], analysis={"ok": True})],
                               ValueError("invalid"), [dict(jobs[2], analysis={"ok": True})],
                               [dict(jobs[3], analysis={"ok": True})]]
        results = enrich_jobs(jobs)
        self.assertEqual(len(results), 4)
        self.assertIn("校验失败", results[1]["analysis_status"])
        self.assertTrue(results[3]["analysis"])

    @patch.dict("os.environ", {"AI_BASE_URL": "https://api.metarouters.org/v1", "AI_API_KEY": "", "OPENAI_API_KEY": "must-not-send"}, clear=True)
    @patch("radar.ai_analysis.analyze_batch")
    def test_alternate_service_never_uses_openai_key(self, analyze):
        self.assertIn("AI未配置", enrich_jobs([{"title": "建筑"}])[0]["analysis_status"])
        analyze.assert_not_called()

    @patch.dict("os.environ", {"AI_BASE_URL": "https://api.metarouters.org/v1", "AI_API_KEY": "test", "AI_MODEL": ""}, clear=True)
    @patch("radar.ai_analysis.analyze_batch")
    def test_alternate_service_requires_model(self, analyze):
        self.assertIn("模型未配置", enrich_jobs([{"title": "建筑"}])[0]["analysis_status"])
        analyze.assert_not_called()

    def test_reject_insecure_endpoint(self):
        with self.assertRaises(ValueError):
            analyze_batch([], {}, "test", "model", "http://example.com/v1")

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
        item.update(index=0, fit_score=80, ai_permission="allowed", permission_evidence="不存在的证据", automation_level="full")
        response = MagicMock()
        response.read.return_value = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"jobs": [item]})}}]}).encode()
        opener.return_value.open.return_value.__enter__.return_value = response
        result = analyze_batch([{"title": "建筑", "description": "招聘建筑专家"}], {}, "fake-test-key", "gpt-5-mini")
        self.assertEqual(result[0]["analysis"]["ai_permission"], "unknown")
        self.assertEqual(result[0]["analysis"]["automation_level"], "partial")
        self.assertEqual(result[0]["analysis_status"], "OpenAI已分析")
        alternate = analyze_batch([{"title": "建筑"}], {}, "provider-test-key", "provider-model", "https://api.metarouters.org/v1")
        self.assertEqual(alternate[0]["analysis_status"], "AI已分析")
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.metarouters.org/v1/chat/completions")
        body = json.loads(request.data)
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertNotIn("reasoning_effort", body)
        self.assertNotIn("store", body)
        self.assertEqual(request.get_header("Authorization"), "Bearer provider-test-key")
        item.update(ai_permission="allowed", permission_evidence="允许AI", automation_level="full", human_review="专业审核")
        response.read.return_value = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"jobs": [item]})}}]}).encode()
        guarded = analyze_batch([{"title": "建筑", "description": "允许AI"}], {}, "test", "model")
        self.assertEqual(guarded[0]["analysis"]["automation_level"], "partial")
        item["index"] = 2
        response.read.return_value = json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"jobs": [item]})}}]}).encode()
        with self.assertRaises(ValueError):
            analyze_batch([{"title": "建筑"}], {}, "fake-test-key", "gpt-5-mini")
