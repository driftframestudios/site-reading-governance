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
secret_shapes = load_tool("scan_secret_shapes")


class GovernancePackageTests(unittest.TestCase):
    def test_schema_catalog_is_coherent(self) -> None:
        self.assertEqual([], validation.validate_schema_catalog())

    def test_every_mapped_example_validates(self) -> None:
        self.assertEqual([], validation.validate_examples())

    def test_root_orientation_records_form_one_coherent_control_surface(self) -> None:
        self.assertEqual([], validation.validate_repository_orientation())

    def test_candidate_provenance_requires_a_settling_promotion_item(self) -> None:
        records = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in validation.ROOT_ORIENTATION_SCHEMAS
        }
        for item in records["coordination-horizon.json"]["work_items"]:
            if item["item_id"] in records["coordination-horizon.json"][
                "current_item_ids"
            ]:
                item["state"] = "active"
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("current settling promotion item" in finding.message for finding in findings),
            findings,
        )

    def test_root_contract_digest_binds_material_contract_file(self) -> None:
        records = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in validation.ROOT_ORIENTATION_SCHEMAS
        }
        records["machine-node.json"]["contracts"][0]["digest"] = (
            "sha256:" + ("f" * 64)
        )
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("must bind" in finding.message for finding in findings),
            findings,
        )

    def test_ruleset_exports_preserve_governed_flow(self) -> None:
        self.assertEqual([], validation.validate_rulesets())

    def test_workflows_use_bounded_permissions_and_immutable_actions(self) -> None:
        self.assertEqual([], validation.validate_workflows())

    def test_release_branch_advances_main(self) -> None:
        self.assertEqual([], branch_flow.check_flow("main", "release/2.0.0"))

    def test_feature_branch_advances_develop(self) -> None:
        self.assertEqual(
            [],
            branch_flow.check_flow("develop", "feature/1042-receipt-contract"),
        )

    def test_forecast_and_evidence_branches_advance_develop(self) -> None:
        self.assertEqual(
            [],
            branch_flow.check_flow("develop", "forecast/2026-q3-r1"),
        )
        self.assertEqual(
            [],
            branch_flow.check_flow("develop", "evidence/rcp-1042-redacted-manifest"),
        )

    def test_release_branch_uses_unprefixed_semver(self) -> None:
        self.assertTrue(branch_flow.check_flow("main", "release/v2.0.0"))

    def test_schema_release_coordinates_are_current(self) -> None:
        self.assertEqual("2.0.0", (ROOT / "VERSION").read_text().strip())
        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            schema = json.loads(path.read_text())
            self.assertTrue(schema["$id"].startswith(validation.SCHEMA_ID_PREFIX))
        mapping = json.loads(
            (ROOT / "examples" / "example-map.json").read_text()
        )["schema_map"]
        for example_name in mapping:
            document = json.loads((ROOT / "examples" / example_name).read_text())
            self.assertEqual(
                validation.SCHEMA_RELEASE,
                document["metadata"]["schema_version"],
            )

    def test_feature_branch_routes_through_develop(self) -> None:
        findings = branch_flow.check_flow("main", "feature/1042-receipt-contract")
        self.assertTrue(findings)

    def test_coordination_vocabulary_uses_generic_horizon(self) -> None:
        self.assertEqual([], validation.validate_coordination_vocabulary())

    def test_probability_names_event_horizon_basis_and_conditions(self) -> None:
        schema = ROOT / "schemas" / "decision.schema.json"
        document = json.loads((ROOT / "examples" / "decision.json").read_text())
        for field in (
            "probability_of",
            "probability_horizon",
            "probability_basis",
            "probability_conditions",
            "recalibration_triggers",
        ):
            candidate = dict(document)
            candidate.pop(field)
            findings = validation.SchemaValidator(schema).validate(candidate)
            self.assertTrue(
                any(field in finding.message for finding in findings),
                (field, findings),
            )

    def test_broad_write_operation_requires_approval(self) -> None:
        schema = ROOT / "schemas" / "operation.schema.json"
        document = json.loads((ROOT / "examples" / "operation.json").read_text())
        document["approval_policy"]["mode"] = "automatic"
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("required" in finding.message for finding in findings),
            findings,
        )

    def test_authorized_broad_write_call_references_approval(self) -> None:
        schema = ROOT / "schemas" / "call-receipt.schema.json"
        document = json.loads(
            (ROOT / "examples" / "call-receipt.json").read_text()
        )
        document["approval_ids"] = []
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("minItems" in finding.message for finding in findings),
            findings,
        )

    def test_simulated_approval_uses_roles_and_simulation_authority(self) -> None:
        schema = ROOT / "schemas" / "approval.schema.json"
        document = json.loads((ROOT / "examples" / "approval.json").read_text())
        self.assertNotIn("authority_actor", document)
        self.assertEqual([], validation.SchemaValidator(schema).validate(document))
        document["authority"] = "organizational"
        findings = validation.SchemaValidator(schema).validate(document)
        messages = " ".join(finding.message for finding in findings)
        self.assertIn("authority_actor", messages)
        self.assertIn("observed", messages)

    def test_simulated_substantive_closure_is_explicitly_bounded(self) -> None:
        schema = ROOT / "schemas" / "simulated-receipt-closure.schema.json"
        document = json.loads(
            (ROOT / "examples" / "simulated-receipt-closure.json").read_text()
        )
        self.assertEqual("closed_in_simulation", document["closure_status"])
        self.assertEqual(
            "separate_unasserted_state",
            document["environment_observed_closure"],
        )
        self.assertEqual("none", document["production_authorization_effect"])
        self.assertEqual([], validation.SchemaValidator(schema).validate(document))
        for field, replacement in (
            ("environment_observed_closure", "closed"),
            ("production_authorization_effect", "production_approved"),
        ):
            candidate = json.loads(json.dumps(document))
            candidate[field] = replacement
            self.assertTrue(
                validation.SchemaValidator(schema).validate(candidate),
                field,
            )

    def test_simulated_closure_covers_four_distinct_families(self) -> None:
        document = json.loads(
            (ROOT / "examples" / "simulated-receipt-closure.json").read_text()
        )
        families = {
            item["family"] for item in document["receipt_closures"]
        }
        self.assertEqual(
            validation.SUBSTANTIVE_SIMULATED_RECEIPT_FAMILIES,
            families,
        )
        document["receipt_closures"][1]["family"] = document[
            "receipt_closures"
        ][0]["family"]
        findings = validation._validate_control_plane_examples(
            {"simulated-receipt-closure.json": document}
        )
        self.assertTrue(
            any("exactly once" in finding.message for finding in findings),
            findings,
        )

    def test_machine_node_and_first_receipt_remain_non_authorizing(self) -> None:
        node_schema = ROOT / "schemas" / "machine-node.schema.json"
        node = json.loads((ROOT / "examples" / "machine-node.json").read_text())
        receipt_schema = ROOT / "schemas" / "first-receipt.schema.json"
        receipt = json.loads(
            (ROOT / "examples" / "first-receipt.json").read_text()
        )
        node["authority"]["mode"] = "production_authority"
        receipt["authority_posture"]["mode"] = "production_authority"
        self.assertTrue(validation.SchemaValidator(node_schema).validate(node))
        self.assertTrue(
            validation.SchemaValidator(receipt_schema).validate(receipt)
        )

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

    def test_non_finite_json_numbers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for token in ("NaN", "Infinity", "-Infinity", "1e10000"):
                path = Path(directory) / f"{token.replace('-', 'negative-')}.json"
                path.write_text(f'{{"confidence": {token}}}', encoding="utf-8")
                with self.assertRaises(validation.NonFiniteNumberError):
                    validation.load_json(path)

        schema = ROOT / "schemas" / "simulation-assumption.schema.json"
        document = json.loads(
            (ROOT / "examples" / "simulation-assumption.json").read_text()
        )
        document["confidence"] = float("nan")
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(any("finite" in finding.message for finding in findings))

    def test_rfc3339_date_times_require_timezones(self) -> None:
        schema = ROOT / "schemas" / "receipt.schema.json"
        document = json.loads((ROOT / "examples" / "receipt.json").read_text())
        for timestamp in ("2026-07-28", "2026-07-28T15:00:00"):
            document["performed_at"] = timestamp
            findings = validation.SchemaValidator(schema).validate(document)
            self.assertTrue(
                any("RFC 3339" in finding.message for finding in findings),
                findings,
            )
        for timestamp in (
            "2026-07-28T15:00:00Z",
            "2026-07-28T15:00:00.125-04:00",
        ):
            document["performed_at"] = timestamp
            self.assertEqual(
                [],
                validation.SchemaValidator(schema).validate(document),
            )

    def test_artifact_locators_are_opaque_governed_references(self) -> None:
        schema = ROOT / "schemas" / "receipt.schema.json"
        document = json.loads((ROOT / "examples" / "receipt.json").read_text())
        unsafe_locators = (
            "https://user:" + "password@example.test/evidence",
            "https://bucket.s3.amazonaws.com/item?X-Amz-Signature=abc",
            "governed://evidence/item?token=abc",
            "governed://user@evidence/item",
            "governed://evidence/item#fragment",
        )
        for locator in unsafe_locators:
            document["artifacts"][0]["locator"] = locator
            findings = validation.SchemaValidator(schema).validate(document)
            self.assertTrue(
                any("pattern" in finding.message for finding in findings),
                findings,
            )
        document["artifacts"][0]["locator"] = "evidence://quality/receipt-001"
        self.assertEqual([], validation.SchemaValidator(schema).validate(document))

    def test_contract_request_paths_are_bounded(self) -> None:
        self.assertEqual(
            [],
            validation.validate_contract_request(
                ROOT,
                ROOT / "examples",
                "receipt.schema.json",
                "receipt.json",
            ),
        )
        for schema_name, document_path in (
            ("receipt.schema.json;echo-value", "receipt.json"),
            ("../receipt.schema.json", "receipt.json"),
            ("receipt.schema.json", "../examples/receipt.json"),
            ("receipt.schema.json", "receipt.json;echo-value"),
        ):
            self.assertTrue(
                validation.validate_contract_request(
                    ROOT,
                    ROOT / "examples",
                    schema_name,
                    document_path,
                )
            )

    def test_secret_shape_findings_redact_values(self) -> None:
        shaped_value = "AK" + "IA" + ("A" * 16)
        findings = secret_shapes.scan_text(
            Path("fixture.env"),
            ("AWS_ACCESS" + f'_KEY_ID="{shaped_value}"\n'),
        )
        self.assertTrue(findings)
        rendered = "\n".join(str(finding) for finding in findings)
        self.assertNotIn(shaped_value, rendered)
        self.assertIn("redacted", rendered)

    def test_runtime_secret_references_are_accepted(self) -> None:
        self.assertEqual(
            [],
            secret_shapes.scan_text(
                Path("fixture.env"),
                'API_KEY="${API_KEY}"\n'
                'PASSWORD="secretsmanager://lims/vendor/password"\n',
            ),
        )

    def test_repository_secret_shape_scan_passes(self) -> None:
        self.assertEqual([], secret_shapes.scan_repository(ROOT))

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
