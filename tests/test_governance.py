"""Regression tests for the governance package."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


validation = load_tool("validate_governance")
language = load_tool("check_language")
branch_flow = load_tool("check_branch_flow")


class GovernancePackageTests(unittest.TestCase):
    def test_schema_catalog_is_coherent(self) -> None:
        self.assertEqual([], validation.validate_schema_catalog())

    def test_every_mapped_example_validates(self) -> None:
        self.assertEqual([], validation.validate_examples())

    def test_ruleset_exports_preserve_governed_flow(self) -> None:
        self.assertEqual([], validation.validate_rulesets())

    def test_workflows_use_bounded_permissions_and_immutable_actions(self) -> None:
        self.assertEqual([], validation.validate_workflows())

    def test_release_branch_advances_main(self) -> None:
        self.assertEqual([], branch_flow.check_flow("main", "release/0.1.0"))

    def test_feature_branch_advances_develop(self) -> None:
        self.assertEqual(
            [],
            branch_flow.check_flow("develop", "feature/1042-receipt-contract"),
        )

    def test_feature_branch_routes_through_develop(self) -> None:
        findings = branch_flow.check_flow("main", "feature/1042-receipt-contract")
        self.assertTrue(findings)

    def test_simulated_receipt_requires_simulation_authority(self) -> None:
        schema = ROOT / "schemas" / "receipt.schema.json"
        document = json.loads((ROOT / "examples" / "receipt.json").read_text())
        document["authority"] = "organizational"
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("simulation_only" in finding.message for finding in findings),
            findings,
        )

    def test_accepted_receipt_requires_observed_organizational_authority(self) -> None:
        schema = ROOT / "schemas" / "receipt.schema.json"
        document = json.loads((ROOT / "examples" / "receipt.json").read_text())
        document["assurance_stage"] = "accepted"
        findings = validation.SchemaValidator(schema).validate(document)
        messages = " ".join(finding.message for finding in findings)
        self.assertIn("accountable_approver", messages)
        self.assertIn("observed", messages)
        self.assertIn("organizational", messages)

    def test_actual_acceptance_uses_observed_evidence(self) -> None:
        schema = ROOT / "schemas" / "acceptance.schema.json"
        document = json.loads((ROOT / "examples" / "acceptance.json").read_text())
        document["authority"] = "actual_accountable"
        findings = validation.SchemaValidator(schema).validate(document)
        messages = " ".join(finding.message for finding in findings)
        self.assertIn("observed", messages)

    def test_unknown_governance_property_is_rejected(self) -> None:
        schema = ROOT / "schemas" / "scenario.schema.json"
        document = json.loads((ROOT / "examples" / "scenario.json").read_text())
        document["surprise"] = "schema drift"
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("outside the contract" in finding.message for finding in findings),
            findings,
        )

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(validation.DuplicateKeyError):
                validation.load_json(path)

    def test_language_check_passes_repository(self) -> None:
        findings = []
        for path in language.repository_files():
            if path.suffix == ".py":
                findings.extend(language.check_python(path))
            else:
                findings.extend(language.check_text(path))
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
