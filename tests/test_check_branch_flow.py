import unittest

from tools import check_branch_flow


class TestCheckBranchFlow(unittest.TestCase):
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
