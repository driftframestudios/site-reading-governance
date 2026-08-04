"""Focused tests for the maintained documentary surface."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
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


class GovernanceDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "examples" / "data-contract.json").read_text(encoding="utf-8")
        )

    def test_maintained_examples_validate_with_jsonschema(self) -> None:
        self.assertEqual([], validation.validate_examples())

    def test_root_orientation_validates_independently(self) -> None:
        self.assertEqual([], validation.validate_repository_orientation())

    def test_machine_node_is_documentary_hydration(self) -> None:
        node = json.loads((ROOT / "machine-node.json").read_text(encoding="utf-8"))
        self.assertEqual("none", node["runtime_effect"])
        self.assertIn("navigation", node)
        self.assertIn("current", node)
        self.assertIn("next", node)
        self.assertIn("later", node)

    def test_data_contract_digest_matches_canonical_material(self) -> None:
        material = dict(self.contract)
        declared = material.pop("contract_digest")
        canonical = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.assertEqual(f"sha256:{hashlib.sha256(canonical).hexdigest()}", declared)

    def test_data_contract_uses_native_enterprise_primitives(self) -> None:
        fields = {
            field["column_name"]: field
            for entity in self.contract["entities"]
            for field in entity["fields"]
        }
        self.assertEqual("timestamptz", fields["collected_at"]["physical_type"])
        self.assertEqual("date", fields["received_date"]["physical_type"])
        self.assertEqual("numeric(38,12)", fields["canonical_value"]["physical_type"])
        self.assertEqual("bytea", fields["source_artifact_digest"]["physical_type"])
        self.assertEqual("uuid", fields["tenant_id"]["physical_type"])

    def test_scientific_quantity_bindings_resolve_to_fields(self) -> None:
        for entity in self.contract["entities"]:
            field_ids = {field["field_id"] for field in entity["fields"]}
            for binding in entity["quantity_bindings"]:
                for key, field_id in binding.items():
                    if key.endswith("_field_id"):
                        self.assertIn(field_id, field_ids, key)

    def test_tenant_entities_use_composite_identity_and_forced_rls(self) -> None:
        for entity in self.contract["entities"]:
            scope = entity["tenant_scope"]
            if scope["scope_mode"] != "tenant_owned":
                continue
            tenant_field = scope["tenant_field_id"]
            self.assertEqual("forced_row_level_security", scope["row_security_mode"])
            self.assertTrue(scope["composite_identity_required"])
            self.assertEqual(tenant_field, entity["primary_key_field_ids"][0])

    def test_refactor_ledger_stays_direct(self) -> None:
        finding = json.loads(
            (ROOT / "examples" / "database-refactor-finding.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("target_state", finding)
        self.assertIn("target_migration_ids", finding)

    def test_workflows_use_standard_json_schema_validation(self) -> None:
        workflows = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        )
        self.assertIn("requirements-dev.txt", workflows)
        self.assertIn("tools/validate_governance.py", workflows)

    def test_vale_is_the_active_language_framework(self) -> None:
        configuration = (ROOT / ".vale.ini").read_text(encoding="utf-8")
        target_rule = (
            ROOT / ".vale" / "styles" / "SiteReading" / "TargetState.yml"
        ).read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("BasedOnStyles = SiteReading", configuration)
        self.assertIn("replacement behavior", target_rule)
        self.assertIn("vale --config=.vale.ini", workflow)
        self.assertNotIn("--no-exit", workflow)
        self.assertNotIn("continue-on-error: true", workflow)

    def test_secret_scanning_uses_github_platform_controls(self) -> None:
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("GitHub secret scanning", security)
        self.assertIn("push protection", security.lower())


if __name__ == "__main__":
    unittest.main()
