import json
import unittest
from radar.cards import card_message


class CardTests(unittest.TestCase):
    def test_actionable_plan_and_human_boundary_are_visible(self):
        analysis = {"fit_score": 80, "summary": "真实案例出题", "requirements": "业务经历",
                    "fit_reason": "专业相关", "risks": "不可编造", "automation_level": "partial",
                    "automation_input": "已授权脱敏案例PDF", "automation_tools": "文档解析+模型API+Python导出",
                    "ai_steps": "解析案例→生成题目→交叉校验→导出文件", "deliverables": "题目和Rubric JSON",
                    "human_review": "核验真实业务与最终答案", "automation_blockers": "无提交接口，手动上传",
                    "ai_permission": "unknown"}
        job = {"title": "企业案例", "analysis": analysis}
        text = json.dumps(card_message([job]), ensure_ascii=False)
        for expected in ("自动化实施方案", "部分自动化", "输入", "工具", "流程", "产出", "你负责", "落地难点", "尚待确认"):
            self.assertIn(expected, text)
        analysis["ai_permission"] = "prohibited"
        text = json.dumps(card_message([job]), ensure_ascii=False)
        self.assertIn("原文限制AI使用", text)
        self.assertNotIn("解析案例→", text)

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
        job["analysis"].update(automation_level="partial", automation_input="长" * 600,
                               automation_tools="长" * 600, automation_blockers="长" * 600,
                               human_review="长" * 600, deliverables="长" * 600)
        payload = card_message([job] * 3)
        self.assertLess(len(json.dumps(payload, ensure_ascii=False).encode()), 17500)
