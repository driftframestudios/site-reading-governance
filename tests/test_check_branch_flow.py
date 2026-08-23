"""Focused regression tests for human and automated branch coordinates."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import unittest

from tools import check_branch_flow


ROOT = Path(__file__).resolve().parents[1]


def workflow_trigger_keys(workflow: str) -> set[str]:
    """Read the exact top-level event keys from a conventionally formatted workflow."""
    lines = workflow.splitlines()
    start = lines.index("on:") + 1
    triggers: set[str] = set()
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        match = re.fullmatch(r"""  ["']?([A-Za-z0-9_-]+)["']?:.*""", line)
        if match:
            triggers.add(match.group(1))
    return triggers


def runner_job_blocks(workflow: str) -> dict[str, str]:
    """Return each job block that allocates a runner."""
    lines = workflow.splitlines()
    start = lines.index("jobs:") + 1
    job_starts = [
        (index, match.group(1))
        for index in range(start, len(lines))
        if (match := re.fullmatch(r"  ([A-Za-z0-9_-]+):", lines[index]))
    ]
    blocks: dict[str, str] = {}
    for position, (index, name) in enumerate(job_starts):
        end = (
            job_starts[position + 1][0]
            if position + 1 < len(job_starts)
            else len(lines)
        )
        block = "\n".join(lines[index:end])
        if re.search(r"(?m)^    runs-on:", block):
            blocks[name] = block
    return blocks


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
            ["--base", "main", "--head", "release/2.0.1"],
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
            base="release/2.0.1",
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

    def test_dependency_activation_template_and_branch_grammar_share_ecosystems(
        self,
    ) -> None:
        config = (ROOT / ".github" / "dependabot.manual.yml").read_text(
            encoding="utf-8"
        )
        self.assertFalse((ROOT / ".github" / "dependabot.yml").exists())
        self.assertIn("Activation template:", config)
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

    def test_workflow_catalog_preserves_human_cued_activation(self) -> None:
        workflow_directory = ROOT / ".github" / "workflows"
        workflow_paths = sorted(
            [*workflow_directory.glob("*.yml"), *workflow_directory.glob("*.yaml")]
        )
        expected_triggers = {
            "validate.yml": {"workflow_dispatch"},
            "reusable-contract-validation.yml": {"workflow_call"},
            "reusable-governance-validation.yml": {"workflow_call"},
        }
        self.assertEqual(sorted(expected_triggers), [path.name for path in workflow_paths])
        workflows = {
            path.name: path.read_text(encoding="utf-8") for path in workflow_paths
        }
        for name, expected in expected_triggers.items():
            with self.subTest(workflow=name):
                self.assertEqual(expected, workflow_trigger_keys(workflows[name]))

        manual_proof = workflows["validate.yml"]
        self.assertFalse(
            (ROOT / ".github" / "workflows" / "branch-policy.yml").exists()
        )
        self.assertIn("permissions:\n  contents: read", manual_proof)
        self.assertIn("confirm_run:", manual_proof)
        self.assertIn("vars.ENABLE_GITHUB_ACTIONS == 'true'", manual_proof)
        self.assertIn("inputs.confirm_run", manual_proof)
        self.assertIn("timeout-minutes: 10", manual_proof)
        jobs = runner_job_blocks(manual_proof)
        self.assertTrue(jobs)
        for name, block in jobs.items():
            with self.subTest(job=name):
                gate = re.search(r"(?m)^    if:\s*(.+)$", block)
                self.assertIsNotNone(gate)
                assert gate is not None
                self.assertIn("vars.ENABLE_GITHUB_ACTIONS == 'true'", gate.group(1))
                self.assertIn("inputs.confirm_run", gate.group(1))

        for name in (
            "reusable-governance-validation.yml",
            "reusable-contract-validation.yml",
        ):
            with self.subTest(reusable_workflow=name):
                reusable = workflows[name]
                self.assertIn("permissions:\n  contents: read", reusable)
                self.assertNotIn("python3 tools/check_branch_flow.py", reusable)

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
