import os
import unittest

from tools import check_branch_flow


class TestCheckBranchFlow(unittest.TestCase):
    def setUp(self):
        # Ensure the environment variable does not interfere with tests unless explicitly set
        os.environ.pop("SKIP_BRANCH_PATTERNS", None)

    def tearDown(self):
        os.environ.pop("SKIP_BRANCH_PATTERNS", None)

    def test_dependabot_is_skipped(self):
        rc = check_branch_flow.main(["--base", "main", "--head", "dependabot/github_actions/actions/setup-python-7.0.0"])
        self.assertEqual(rc, 0)

    def test_renovate_is_skipped(self):
        rc = check_branch_flow.main(["--base", "main", "--head", "renovate/major-package-update"])
        self.assertEqual(rc, 0)

    def test_feature_to_main_fails(self):
        rc = check_branch_flow.main(["--base", "main", "--head", "feature/new-ui"])
        # feature/ -> main is not allowed by GitFlow rules in this repo
        self.assertNotEqual(rc, 0)

    def test_custom_pattern_env_var_skips(self):
        # Set a custom skip pattern and ensure it takes effect (overrides default)
        os.environ["SKIP_BRANCH_PATTERNS"] = r"^auto-update/"
        rc = check_branch_flow.main(["--base", "main", "--head", "auto-update/some-deps"])
        self.assertEqual(rc, 0)
        # Ensure default patterns are not used when the env var is set
        rc2 = check_branch_flow.main(["--base", "main", "--head", "dependabot/abc"])
        self.assertNotEqual(rc2, 0)
