import os
import unittest
from unittest.mock import patch
from radar.corexpert import collect_corexpert, normalize, CoreSessionRequired


class CoreXpertTests(unittest.TestCase):
    def test_normalize_and_remove_internal_fields(self):
        row = {"Card": {"CardID": "one", "OutReach": {"Status": 2, "Name": "Test",
               "Description": "<p>图像评测</p>", "RequiredInfo": "本科", "CreatedTime": "1793963178",
               "CreatorID": "not-kept", "QRCode": "not-kept"}}}
        job = normalize(row)
        self.assertIn("图像评测", job["description"])
        self.assertNotIn("CreatorID", job)
        row["Card"]["OutReach"]["Status"] = 1
        self.assertIsNone(normalize(row))

    @patch.dict(os.environ, {"COREXPERT_COOKIE": ""})
    def test_missing_cookie(self):
        with self.assertRaises(CoreSessionRequired):
            collect_corexpert({})

    @patch.dict(os.environ, {"COREXPERT_COOKIE": "test=placeholder"})
    @patch("radar.corexpert.request_page", return_value={"Cards": [], "Total": 2})
    def test_incomplete_list_is_failure(self, request):
        with self.assertRaises(ValueError):
            collect_corexpert({})
