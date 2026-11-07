import unittest
from radar.corexpert_digest import suitability, build_digest


class CoreDigestTests(unittest.TestCase):
    def test_specialist_gate(self):
        self.assertIsNone(suitability({"title": "金融专家", "description": "多模态影视评测"}))
        self.assertIsNotNone(suitability({"title": "图像评审", "description": "图像质量"}))
        self.assertIsNone(suitability({"title": "数字IC前端设计", "description": "设计多模态评测评分标准"}))
        self.assertIsNone(suitability({"title": "能源专家", "description": "设计影视评测评分标准"}))

    def test_requirements_and_summary(self):
        sections, selected = build_digest([{"title": "多学科", "description": "设计评测任务。 要求：视觉传达",
                                            "qualification": "本科以上，视觉传达设计", "salary": "100元"}])
        self.assertEqual(len(selected), 1)
        self.assertIn("本科以上", "\n".join(sections))
