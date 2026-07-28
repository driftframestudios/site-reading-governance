"""Focused regression tests for human and automated branch coordinates."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import unittest

from tools import check_branch_flow


ROOT = Path(__file__).resolve().parents[1]


class BranchFlowAutomationTests(unittest.TestCase):
    def invoke(self, *, base: str, head: str, author: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            result = check_branch_flow.main(
                [
                    "--base",
                    base,
                    "--head",
                    head,
                    "--author",
                    author,
                ]
            )
        return result, output.getvalue()

    def test_non_pull_request_event_skips_with_empty_coordinates(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = check_branch_flow.main([])
        self.assertEqual(0, result)
        self.assertIn("non-pull-request event", output.getvalue())

    def test_partial_pull_request_coordinates_fail_closed(self) -> None:
        for arguments in (
            ["--base", "main", "--head", "release/2.0.0"],
            ["--author", "repository-contributor"],
            ["--base", "main", "--author", "repository-contributor"],
        ):
            with self.subTest(arguments=arguments):
                output = StringIO()
                with redirect_stdout(output):
                    result = check_branch_flow.main(arguments)
                self.assertEqual(2, result)
                self.assertIn(
                    "requires base, head, and pull-request author",
                    output.getvalue(),
                )

    def test_dependabot_branch_is_admitted_for_its_bot_author(self) -> None:
        result, output = self.invoke(
            base="main",
            head="dependabot/github_actions/actions/setup-python-7.0.0",
            author="dependabot[bot]",
        )
        self.assertEqual(0, result)
        self.assertIn("Dependabot branch", output)

    def test_renovate_branch_is_admitted_for_its_bot_author(self) -> None:
        result, output = self.invoke(
            base="develop",
            head="renovate/github-actions-minor",
            author="renovate[bot]",
        )
        self.assertEqual(0, result)
        self.assertIn("Renovate branch", output)

    def test_self_hosted_renovate_identity_requires_reviewed_policy(self) -> None:
        result, output = self.invoke(
            base="main",
            head="renovate/github-actions-minor",
            author="self-hosted-renovate[bot]",
        )
        self.assertEqual(1, result)
        self.assertIn("requires pull-request author renovate[bot]", output)

    def test_automation_looking_branch_preserves_author_binding(self) -> None:
        result, output = self.invoke(
            base="main",
            head="dependabot/github_actions/actions/checkout-5.0.0",
            author="repository-contributor",
        )
        self.assertEqual(1, result)
        self.assertIn("requires pull-request author", output)

    def test_automation_branch_preserves_allowed_target_binding(self) -> None:
        result, output = self.invoke(
            base="release/2.0.0",
            head="dependabot/github_actions/actions/checkout-5.0.0",
            author="dependabot[bot]",
        )
        self.assertEqual(1, result)
        self.assertIn("should target one of develop, main", output)

    def test_dependabot_grammar_reflects_configured_ecosystem(self) -> None:
        result, output = self.invoke(
            base="main",
            head="dependabot/pip/setuptools-80.0.0",
            author="dependabot[bot]",
        )
        self.assertEqual(1, result)
        self.assertIn("outside the branch naming contract", output)

    def test_dependabot_config_and_branch_grammar_share_ecosystems(self) -> None:
        config = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        configured = {
            ecosystem.replace("-", "_")
            for ecosystem in re.findall(
                r"^\s*-\s+package-ecosystem:\s*[\"']?([a-z0-9-]+)",
                config,
                flags=re.MULTILINE,
            )
        }
        self.assertEqual(check_branch_flow.DEPENDABOT_BRANCH_ECOSYSTEMS, configured)
        self.assertNotIn("pull-request-branch-name:", config)

    def test_branch_policy_executes_only_the_base_controlled_checker(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "branch-policy.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", workflow)
        self.assertIn(
            "ref: ${{ github.event.pull_request.base.sha }}",
            workflow,
        )
        self.assertIn("path: .branch-policy-base", workflow)
        self.assertIn("sparse-checkout: tools/check_branch_flow.py", workflow)
        self.assertIn("sparse-checkout-cone-mode: false", workflow)
        self.assertIn("working-directory: .branch-policy-base", workflow)
        self.assertIn(
            "PR_AUTHOR: ${{ github.event.pull_request.user.login }}",
            workflow,
        )
        self.assertIn('--author "$PR_AUTHOR"', workflow)
        self.assertEqual(1, workflow.count("actions/checkout@"))
        self.assertNotIn("github.event.pull_request.head.sha", workflow)

        for name in ("validate.yml", "reusable-governance-validation.yml"):
            with self.subTest(head_validation_workflow=name):
                head_validation = (
                    ROOT / ".github" / "workflows" / name
                ).read_text(encoding="utf-8")
                self.assertNotIn("pull_request_target:", head_validation)
                self.assertNotIn("PR_AUTHOR:", head_validation)
                self.assertNotIn(
                    "python3 tools/check_branch_flow.py",
                    head_validation,
                )

    def test_automation_grammar_rejects_noncanonical_segments(self) -> None:
        for head in (
            "dependabot/github_actions/actions/../release",
            "dependabot/github_actions/actions//checkout-5.0.0",
            "renovate/.hidden-topic",
        ):
            with self.subTest(head=head):
                result, output = self.invoke(
                    base="main",
                    head=head,
                    author="dependabot[bot]",
                )
                self.assertEqual(1, result)
                self.assertIn("outside the branch naming contract", output)

    def test_feature_branch_retains_gitflow_routing(self) -> None:
        result, output = self.invoke(
            base="main",
            head="feature/new-ui",
            author="repository-contributor",
        )
        self.assertEqual(1, result)
        self.assertIn("should use one of release/, hotfix/", output)


if __name__ == "__main__":
    unittest.main()
