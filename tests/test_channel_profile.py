import json
import unittest
from pathlib import Path

from src.validate_channel_profile import PROFILE, validate


class ChannelProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_committed_profile_passes(self):
        self.assertEqual(validate(self.profile), [])

    def test_copying_is_blocked(self):
        profile = json.loads(json.dumps(self.profile))
        profile["editorial_rules"]["copy_other_account_scripts"] = True
        self.assertTrue(validate(profile))

    def test_public_autopublish_is_blocked_by_default(self):
        profile = json.loads(json.dumps(self.profile))
        profile["production_constraints"]["automatic_public_upload_enabled"] = True
        self.assertTrue(validate(profile))

    def test_paid_tools_are_blocked(self):
        profile = json.loads(json.dumps(self.profile))
        profile["production_constraints"]["paid_apis_or_credits"] = True
        self.assertTrue(validate(profile))


if __name__ == "__main__":
    unittest.main()
