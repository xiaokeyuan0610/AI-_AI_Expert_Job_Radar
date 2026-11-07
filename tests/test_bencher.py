import unittest
from radar.bencher import parse_jobs
from radar.core import identity


class BencherTests(unittest.TestCase):
    def test_real_schema_and_distinct_links(self):
        jobs = parse_jobs({"code": 200, "data": {"total": 2, "list": [
            {"id": 103, "title": "Video", "summary": "Vlog", "salary": "100元/份"},
            {"id": 71, "title": "Blender", "summary": "5年经验"}]}})
        self.assertNotEqual(identity(jobs[0]), identity(jobs[1]))
        self.assertEqual(jobs[0]["salary"], "100元/份")

    def test_reject_partial_and_login_response(self):
        for payload in [{"code": 401}, {"code": 200, "data": {"total": 12, "list": []}}]:
            with self.assertRaises(ValueError):
                parse_jobs(payload)

    def test_valid_empty(self):
        self.assertEqual(parse_jobs({"code": 200, "data": {"total": 0, "list": []}}), [])
