import unittest
from unittest.mock import patch
from radar.public_sources import collect_public, normalize
from radar.core import identity


class PublicSourcesTests(unittest.TestCase):
    def test_closed_and_data_minimization(self):
        row = {"recruitmentId": "one", "recruitmentName": "Video", "recruitmentStatus": "COMPLETED"}
        self.assertIsNone(normalize("appen_public", row))
        row.update(recruitmentStatus="RUNNING", applicationCandidates=[{"private": "ignored"}], description="<p>Test &amp; video</p>")
        job = normalize("appen_public", row)
        self.assertNotIn("applicationCandidates", job)
        self.assertEqual(job["description"], "Test & video")
        other = dict(job, source_id="appen_public:two")
        self.assertNotEqual(identity(job), identity(other))

    @patch("radar.public_sources.time.sleep")
    @patch("radar.public_sources.fetch")
    def test_pagination(self, fetch, sleep):
        def page(identifier):
            return {"status_code": 0, "data": {"count": 2, "items": [{"id": identifier, "title": "Test", "online_status": 10}]}}
        fetch.side_effect = [page(1), page(2)]
        self.assertEqual(len(collect_public({"method": "fellow_public"})), 2)
        fetch.side_effect = [page(1), page(1)]
        with self.assertRaises(ValueError):
            collect_public({"method": "fellow_public"})

    @patch("radar.public_sources.fetch", return_value={"success": False})
    def test_auth_failure(self, fetch):
        with self.assertRaises(ValueError):
            collect_public({"method": "talents_public"})
