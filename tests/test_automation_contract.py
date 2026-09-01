"""Mutation tests for the fail-closed pull-request automation contract."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools import automation_contract


ROOT = Path(__file__).resolve().parents[1]
USE_CURRENT_CONTROLS = object()


class AutomationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = (
            ROOT / ".github" / "workflows" / "pull-request.yml"
        ).read_text(encoding="utf-8")
        cls.dependabot = (ROOT / ".github" / "dependabot.yml").read_text(
            encoding="utf-8"
        )
        cls.automation_controls = json.loads(
            (ROOT / ".github" / "automation-controls.json").read_text(
                encoding="utf-8"
            )
        )

    def findings(
        self,
        *,
        workflow: str | None = None,
        dependabot: str | None = None,
        declared_controls: object = USE_CURRENT_CONTROLS,
    ) -> list[str]:
        return automation_contract.validate_repository_automation(
            self.workflow if workflow is None else workflow,
            self.dependabot if dependabot is None else dependabot,
            (
                self.automation_controls
                if declared_controls is USE_CURRENT_CONTROLS
                else declared_controls
            ),
        )

    def changed(self, source: str, old: str, new: str) -> str:
        self.assertIn(old, source)
        return source.replace(old, new, 1)

    def assert_rejected(
        self,
        findings: list[str],
        expected: str,
    ) -> None:
        self.assertTrue(
            any(expected in finding for finding in findings),
            f"expected {expected!r} in {findings!r}",
        )

    def test_current_files_and_complete_local_proof_match_contract(self) -> None:
        self.assertEqual([], self.findings())
        self.assertEqual(
            (
                "python3 tools/validate_governance.py",
                "python3 tools/check_language.py",
                "python3 tools/scan_secret_shapes.py",
                "python3 -m unittest discover -s tests -v",
            ),
            automation_contract.PULL_REQUEST_CONTRACT.validation_commands,
        )
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "/tools/automation_contract.py @driftframestudios",
            codeowners,
        )
        self.assertIn(
            "/.github/automation-controls.json @driftframestudios",
            codeowners,
        )

    def test_required_commands_cannot_survive_only_as_comments_or_variants(self) -> None:
        aggregate = "          python3 tools/validate_governance.py"
        mutations = (
            (
                "comment-only",
                self.changed(
                    self.workflow,
                    aggregate,
                    "          # python3 tools/validate_governance.py\n          true",
                ),
            ),
            (
                "wrong-command",
                self.changed(
                    self.workflow,
                    aggregate,
                    "          python3 tools/validate_governance.py --wrong",
                ),
            ),
        )
        for name, workflow in mutations:
            with self.subTest(name=name):
                self.assert_rejected(
                    self.findings(workflow=workflow),
                    "validation commands differ",
                )

    def test_permissions_cannot_broaden_or_move_to_a_job_override(self) -> None:
        mutations = (
            (
                "workflow-write",
                self.changed(
                    self.workflow,
                    "permissions:\n  contents: read",
                    "permissions:\n  contents: write",
                ),
                "permissions must be exactly",
            ),
            (
                "job-override",
                self.changed(
                    self.workflow,
                    "    timeout-minutes: 10",
                    "    timeout-minutes: 10\n    permissions:\n      contents: write",
                ),
                "override permissions",
            ),
        )
        for name, workflow, expected in mutations:
            with self.subTest(name=name):
                self.assert_rejected(self.findings(workflow=workflow), expected)

    def test_validation_step_cannot_fail_open(self) -> None:
        workflow = self.changed(
            self.workflow,
            "      - name: Validate repository-owned governance\n        run:",
            "      - name: Validate repository-owned governance\n"
            "        continue-on-error: true\n"
            "        run:",
        )
        self.assert_rejected(
            self.findings(workflow=workflow),
            "repository validation step controls differ",
        )

    def test_unsupported_or_ambiguous_yaml_fails_closed(self) -> None:
        workflow_mutations = (
            self.changed(
                self.workflow,
                "permissions:\n  contents: read",
                "permissions: {contents: read}",
            ),
            self.workflow + "\nname: duplicate\n",
            self.changed(self.workflow, "        run: |", "        run: >"),
            self.changed(self.workflow, "permissions:", '"permissions":'),
        )
        for workflow in workflow_mutations:
            with self.subTest(source="workflow"):
                self.assert_rejected(
                    self.findings(workflow=workflow),
                    "outside the restricted YAML grammar",
                )

        dependabot = self.changed(
            self.dependabot,
            "    schedule:\n      interval: monthly",
            "    schedule: {interval: monthly}",
        )
        self.assert_rejected(
            self.findings(dependabot=dependabot),
            "Dependabot configuration is outside the restricted YAML grammar",
        )
        quoted_dependabot = self.changed(
            self.dependabot,
            "package-ecosystem: github-actions",
            '"package-ecosystem": github-actions',
        )
        self.assert_rejected(
            self.findings(dependabot=quoted_dependabot),
            "Dependabot configuration is outside the restricted YAML grammar",
        )

    def test_quoted_and_unknown_controls_are_consumed_not_skipped(self) -> None:
        quoted_secret_control = self.changed(
            self.workflow,
            "\njobs:\n",
            '\n"env":\n  TOKEN: "${{ secrets[\'TOKEN\'] }}"\n\njobs:\n',
        )
        self.assert_rejected(
            self.findings(workflow=quoted_secret_control),
            "outside the restricted YAML grammar",
        )
        unknown_control = self.workflow + "\nunexpected-control: true\n"
        self.assert_rejected(
            self.findings(workflow=unknown_control),
            "top-level controls differ",
        )

    def test_cancellation_and_timeout_are_bounded(self) -> None:
        mutations = (
            (
                self.changed(
                    self.workflow,
                    "cancel-in-progress: true",
                    "cancel-in-progress: false",
                ),
                "cancel superseded",
            ),
            (
                self.changed(
                    self.workflow,
                    "timeout-minutes: 10",
                    "timeout-minutes: 11",
                ),
                "timeout ceiling",
            ),
        )
        for workflow, expected in mutations:
            with self.subTest(expected=expected):
                self.assert_rejected(self.findings(workflow=workflow), expected)

    def test_job_catalog_and_action_coordinates_are_exact(self) -> None:
        checkout_sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
        setup_sha = "5fda3b95a4ea91299a34e894583c3862153e4b97"
        mutations = (
            (
                "extra-job",
                self.workflow
                + "\n  unexpected:\n    uses: ./.github/workflows/validate.yml\n",
                "exactly one owned job",
            ),
            (
                "unpinned",
                self.changed(
                    self.workflow,
                    f"actions/checkout@{checkout_sha}",
                    "actions/checkout@v4",
                ),
                "approved GitHub-owned action SHA",
            ),
            (
                "unapproved-full-sha",
                self.changed(
                    self.workflow,
                    f"actions/checkout@{checkout_sha}",
                    "actions/checkout@0000000000000000000000000000000000000000",
                ),
                "approved GitHub-owned action SHA",
            ),
            (
                "third-party-full-sha",
                self.changed(
                    self.workflow,
                    f"actions/checkout@{checkout_sha}",
                    f"third-party/checkout@{checkout_sha}",
                ),
                "approved GitHub-owned action SHA",
            ),
            (
                "unapproved-setup-full-sha",
                self.changed(
                    self.workflow,
                    f"actions/setup-python@{setup_sha}",
                    "actions/setup-python@0000000000000000000000000000000000000000",
                ),
                "approved GitHub-owned action SHA",
            ),
            (
                "anonymous-step",
                self.changed(
                    self.workflow,
                    "      - name: Check out the proposed source\n        uses:",
                    "      - uses:",
                ),
                "checkout step controls differ",
            ),
        )
        for name, workflow, expected in mutations:
            with self.subTest(name=name):
                self.assert_rejected(self.findings(workflow=workflow), expected)

    def test_step_names_and_raw_secret_values_are_rejected(self) -> None:
        step_names = (
            "Check out the proposed source",
            "Select Python",
            "Validate repository-owned governance",
        )
        for step_name in step_names:
            with self.subTest(step_name=step_name, mutation="name-drift"):
                mutated = self.changed(
                    self.workflow,
                    f"      - name: {step_name}",
                    f"      - name: Changed {step_name}",
                )
                self.assert_rejected(
                    self.findings(workflow=mutated),
                    "step name differs",
                )
            with self.subTest(step_name=step_name, mutation="bracket-secret"):
                mutated = self.changed(
                    self.workflow,
                    f"      - name: {step_name}",
                    "      - name: ${{ secrets['AUTOMATION_TOKEN'] }}",
                )
                self.assert_rejected(
                    self.findings(workflow=mutated),
                    "raw GitHub secret expressions",
                )

        value_mutations = (
            self.changed(
                self.workflow,
                "name: Governance pull request",
                "name: ${{ secrets.GOVERNANCE_TOKEN }}",
            ),
            self.changed(
                self.workflow,
                '          python-version: "3.13"',
                '          python-version: "${{ secrets[\'PYTHON_VERSION\'] }}"',
            ),
            self.changed(
                self.workflow,
                "          python3 tools/check_language.py",
                "          echo ${{ secrets.LANGUAGE_TOKEN }}",
            ),
        )
        for workflow in value_mutations:
            with self.subTest(mutation="nested-value-secret"):
                self.assert_rejected(
                    self.findings(workflow=workflow),
                    "raw GitHub secret expressions",
                )

    def test_source_projection_is_required_and_source_derived(self) -> None:
        cases = (
            (
                "missing",
                automation_contract.MISSING_AUTOMATION_CONTROLS,
                "projection is missing",
            ),
            ("null", None, "must not be null"),
        )
        for name, declared, expected in cases:
            with self.subTest(name=name):
                self.assert_rejected(
                    self.findings(declared_controls=declared),
                    expected,
                )

        drifted = deepcopy(self.automation_controls)
        drifted["pull_request"]["job"]["timeout_minutes"] = 9
        self.assert_rejected(
            self.findings(declared_controls=drifted),
            "differs from parsed source controls",
        )

    def test_trigger_allowlist_is_exact(self) -> None:
        mutations = (
            self.changed(
                self.workflow,
                "  pull_request:",
                "  pull_request_target:",
            ),
            self.changed(self.workflow, "      - main\n", ""),
        )
        for workflow in mutations:
            with self.subTest():
                self.assert_rejected(
                    self.findings(workflow=workflow),
                    "trigger must target exactly develop and main",
                )

    def test_dependabot_update_record_is_exact(self) -> None:
        mutations = (
            self.changed(
                self.dependabot,
                "    target-branch: develop",
                "    target-branch: main\n    # target-branch: develop",
            ),
            self.changed(self.dependabot, "interval: monthly", "interval: weekly"),
            self.changed(
                self.dependabot,
                "open-pull-requests-limit: 2",
                "open-pull-requests-limit: 3",
            ),
            self.changed(
                self.dependabot,
                "package-ecosystem: github-actions",
                "package-ecosystem: pip",
            ),
            self.changed(
                self.dependabot,
                "github-actions-minor-patch:",
                "github-actions-all:",
            ),
            self.dependabot
            + "\n  - package-ecosystem: github-actions\n"
            + "    directory: /nested\n"
            + "    target-branch: develop\n"
            + "    schedule:\n"
            + "      interval: monthly\n"
            + "    open-pull-requests-limit: 1\n",
        )
        for dependabot in mutations:
            with self.subTest():
                self.assert_rejected(
                    self.findings(dependabot=dependabot),
                    "exactly the declared monthly develop update record",
                )


if __name__ == "__main__":
    unittest.main()
