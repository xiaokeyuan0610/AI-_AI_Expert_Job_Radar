import json
import unittest
from pathlib import Path
from radar.core import score, message
from radar.corexpert_digest import suitability
from radar.recommendations import recommendation, ai_workflow


class RecommendationTests(unittest.TestCase):
    def test_text_and_history_can_match_independently(self):
        rules = json.loads(Path("config/matching.json").read_text(encoding="utf-8"))
        for title in ("中文写作专家", "文案校对", "文本质量评测", "世界史专家", "通史出题", "历史学专家"):
            job = {"title": title, "description": "任务要求待确认"}
            self.assertGreaterEqual(score(job, rules)[0], rules["threshold"])
            self.assertIsNotNone(suitability(job))
        for title in ("历史记录数据库", "代码编辑器开发"):
            self.assertEqual(score({"title": title, "description": ""}, rules)[0], 0)

    def test_architecture_and_interior_included(self):
        rules = json.loads(Path("config/matching.json").read_text(encoding="utf-8"))
        for title in ("建筑设计专家", "室内设计评审", "空间规划", "Revit模型审核"):
            job = {"title": title, "description": "专业评测"}
            self.assertGreaterEqual(score(job, rules)[0], rules["threshold"])
            self.assertIsNotNone(suitability(job))

    def test_five_stars_requires_confirmed_qualification(self):
        job = {"title": "室内设计专家", "description": ""}
        self.assertTrue(recommendation(job).startswith("★★★★☆"))
        self.assertTrue(recommendation(dict(job, qualification_confirmed=True, salary="100元/小时", deadline="2099-01-01")).startswith("★★★★★"))
        self.assertTrue(recommendation(dict(job, qualification_confirmed=False)).startswith("★★☆☆☆"))

    def test_both_messages_have_visual_rating_and_workflow(self):
        job = {"title": "建筑评测", "description": "设计方案", "url": "https://example.com"}
        text = message([job], [])["content"]["text"]
        self.assertIn("★★★★☆", text)
        self.assertIn("AI参与", text)
        self.assertIn("你核验", ai_workflow(job))
