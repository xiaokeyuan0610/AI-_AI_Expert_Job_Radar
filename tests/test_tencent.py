import os
import unittest
from unittest.mock import patch
from radar.tencent import collect_tencent, normalize, LoginRequired


class TencentTests(unittest.TestCase):
    def test_status_and_expired_deadline(self):
        self.assertIsNone(normalize({"status": "ended"}))
        self.assertIsNone(normalize({"signup_deadline": "2020-01-01 00:00:00"}))

    @patch.dict(os.environ, {"TLABEL_COOKIE": ""})
    def test_missing_session(self):
        with self.assertRaises(LoginRequired):
            collect_tencent({})

    @patch.dict(os.environ, {"TLABEL_COOKIE": "test=redacted"})
    @patch("radar.tencent.request_page")
    def test_job_fields_and_pagination(self, request):
        row = {"package_id": 17, "package_name": "文娱", "summary": "影视评测",
               "unit_price": 1000, "unit": "题", "private_account_data": "ignored"}
        request.return_value = {"total": 1, "list": [row]}
        jobs = collect_tencent({})
        self.assertEqual(jobs[0]["salary"], "1000元/题")
        self.assertNotIn("private_account_data", jobs[0])
