import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from radar.profile import load_profile


class ProfileTests(unittest.TestCase):
    @patch.dict("os.environ", {"USER_PROFILE_JSON": json.dumps({"education": ["建筑学硕士"], "phone": "private-contact", "raw_resume": "private-document"})})
    def test_secret_priority_and_contact_exclusion(self):
        self.assertEqual(load_profile(Path("nonexistent")), {"education": ["建筑学硕士"]})

    @patch.dict("os.environ", {"USER_PROFILE_JSON": ""})
    def test_local_private_profile_overrides_generic(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "profile.json").write_text('{"interests": ["generic"]}')
            (directory / "profile.private.json").write_text('{"skills": ["private-skill"]}')
            self.assertEqual(load_profile(directory), {"skills": ["private-skill"], "interests": ["generic"]})

    @patch.dict("os.environ", {"USER_PROFILE_JSON": '{"education":["private-degree"],"interests":["original"],"phone":"private"}'})
    def test_new_preferences_reach_secret_profile_without_exposing_private_facts(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "profile.json").write_text('{"interests":["new-writing-interest"]}')
            result = load_profile(directory)
            self.assertEqual(result["interests"], ["new-writing-interest", "original"])
            self.assertEqual(result["education"], ["private-degree"])
            self.assertNotIn("phone", result)

    @patch.dict("os.environ", {"USER_PROFILE_JSON": "invalid"})
    def test_invalid_secret_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            load_profile()
