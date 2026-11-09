import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location("cloud_timer", Path("deploy/cloud_timer/index.py"))
timer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timer)


class CloudTimerTests(TestCase):
    @patch.dict("os.environ", {"GITHUB_DISPATCH_TOKEN": "test", "GITHUB_REPOSITORY": "owner/repo"})
    @patch.object(timer.urllib.request, "build_opener")
    def test_acceptance_is_not_claimed_as_delivery(self, opener):
        response = MagicMock(status=204)
        opener.return_value.open.return_value.__enter__.return_value = response
        result = timer.main_handler({"Type": "Timer"}, None)
        self.assertFalse(result["delivery_verified"])
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/owner/repo/actions/workflows/radar.yml/dispatches")

    def test_reject_non_timer(self):
        with self.assertRaises(ValueError):
            timer.main_handler({}, None)
