"""Focused contracts for the promotion-receipt projection pilot."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable
import unittest

from graphql import build_ast_schema, parse
from graphql.utilities import coerce_input_value

from tools import schema_projections
from tools import validate_governance


ROOT = Path(__file__).resolve().parents[1]


class SchemaProjectionTests(unittest.TestCase):
    def assert_graphql_source_mutation_rejected(
        self,
        mutation: Callable[[dict[str, Any]], None],
        message_pattern: str,
        *,
        source_document: str = schema_projections.SOURCE_SCHEMA_PATH,
        regenerate_ledger: bool = False,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(
                ROOT / "schema-projections",
                root / "schema-projections",
            )
            source_path = root / source_document
            source = json.loads(source_path.read_text(encoding="utf-8"))
            mutation(source)
            source_path.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            if regenerate_ledger:
                coverage_path = root / schema_projections.COVERAGE_SOURCE_PATH
                coverage_path.write_bytes(
                    schema_projections.render_coverage_ledger(root)
                )
                schema_projections.validate_coverage_ledger(root)
            with self.assertRaisesRegex(
                schema_projections.ProjectionError,
                message_pattern,
            ):
                schema_projections.validate_graphql_projection(root)

    def test_yaml_generation_is_byte_stable_and_semantically_equal(self) -> None:
        first = schema_projections.build_yaml_projection(ROOT)
        second = schema_projections.build_yaml_projection(ROOT)
        source = schema_projections.load_json(
            ROOT / schema_projections.SOURCE_SCHEMA_PATH
        )

        self.assertEqual(first, second)
        self.assertTrue(first.startswith(b"%YAML 1.2\n---\n"))
        self.assertEqual(
            schema_projections.canonical_json(source),
            schema_projections.canonical_json(
                schema_projections.load_yaml_model(first)
            ),
        )

    def test_yaml_preserves_ambiguous_strings_and_unicode(self) -> None:
        model = {
            "boolean-shaped": "true",
            "colon-and-comment": "value: still text # still text",
            "leading-zero": "0123",
            "null-shaped": "null",
            "timestamp-shaped": "2026-09-04T12:34:56Z",
            "unicode": "Δ evidence",
        }
        content = schema_projections.render_yaml_model(model)
        self.assertEqual(model, schema_projections.load_yaml_model(content))

    def test_yaml_profile_rejects_ambiguous_composition_features(self) -> None:
        invalid_documents = {
            "alias": b'a: &shared "value"\nb: *shared\n',
            "duplicate": b'a: "first"\na: "second"\n',
            "explicit-tag": b'a: !thing "value"\n',
            "multiple-documents": b'---\na: "first"\n---\na: "second"\n',
        }
        for name, content in invalid_documents.items():
            with self.subTest(name=name):
                with self.assertRaises(schema_projections.ProjectionError):
                    schema_projections.load_yaml_model(content)

    def test_graphql_sdl_composes_with_the_exact_bounded_shape(self) -> None:
        content = schema_projections.validate_graphql_projection(ROOT)
        schema = build_ast_schema(parse(content.decode("utf-8")))
        self.assertEqual("SchemaProjectionQuery", schema.query_type.name)
        self.assertIsNone(schema.mutation_type)
        self.assertIsNone(schema.subscription_type)
        for type_name, fields in schema_projections.EXPECTED_GRAPHQL_FIELDS.items():
            self.assertEqual(
                fields,
                {
                    name: str(field.type)
                    for name, field in schema.get_type(type_name).fields.items()
                },
            )

    def test_graphql_sdl_rejects_an_unreviewed_definition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(
                ROOT / "schema-projections",
                root / "schema-projections",
            )
            graphql_path = root / schema_projections.GRAPHQL_SOURCE_PATH
            graphql_path.write_text(
                graphql_path.read_text(encoding="utf-8")
                + "\ntype UnreviewedSurface { value: String }\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                schema_projections.ProjectionError,
                "definition inventory differs",
            ):
                schema_projections.validate_graphql_projection(root)

    def test_graphql_binding_rejects_a_new_source_enum_value(self) -> None:
        def add_enum_value(source: dict[str, Any]) -> None:
            source["properties"]["promotion_state"]["enum"].append(
                "withdrawal_observed"
            )

        self.assert_graphql_source_mutation_rejected(
            add_enum_value,
            "GraphQL enum PromotionState values need to match the source",
        )

    def test_graphql_binding_rejects_a_changed_reference_target(self) -> None:
        def change_reference(source: dict[str, Any]) -> None:
            source["properties"]["promotion_receipt_id"]["$ref"] = (
                "common.schema.json#/$defs/semver"
            )

        self.assert_graphql_source_mutation_rejected(
            change_reference,
            r"PromotionReceipt\.promotion_receipt_id needs type SemanticVersion!",
        )

    def test_graphql_binding_rejects_a_required_field_becoming_optional(self) -> None:
        def remove_required_evidence(source: dict[str, Any]) -> None:
            source["required"].remove("required_evidence")

        self.assert_graphql_source_mutation_rejected(
            remove_required_evidence,
            r"PromotionReceipt.required_evidence needs type \[String!\] ",
        )

    def test_graphql_binding_rejects_a_primitive_becoming_a_list(self) -> None:
        def change_accountable_role_shape(source: dict[str, Any]) -> None:
            source["properties"]["accountable_role"] = {
                "type": "array",
                "items": {"type": "string"},
            }

        self.assert_graphql_source_mutation_rejected(
            change_accountable_role_shape,
            r"PromotionReceipt.accountable_role needs type \[String!\]!",
        )

    def test_graphql_binding_retains_required_but_nullable_source_fields(self) -> None:
        content = schema_projections.validate_graphql_projection(ROOT)
        schema = build_ast_schema(parse(content.decode("utf-8")))
        source = schema_projections.load_json(
            ROOT / schema_projections.SOURCE_SCHEMA_PATH
        )
        release_coordinate = source["properties"]["release_coordinate"]
        release_record = release_coordinate["oneOf"][1]
        hosted_receipt = release_record["properties"][
            "hosted_automation_receipt"
        ]
        observed_types = {
            "PromotionReceipt.release_coordinate": str(
                schema.get_type("PromotionReceipt").fields["release_coordinate"].type
            ),
            "ReleaseCoordinate.hosted_automation_receipt": str(
                schema.get_type("ReleaseCoordinate").fields[
                    "hosted_automation_receipt"
                ].type
            ),
        }

        self.assertIn("release_coordinate", source["required"])
        self.assertEqual("null", release_coordinate["oneOf"][0]["type"])
        self.assertIn("hosted_automation_receipt", release_record["required"])
        self.assertEqual("null", hosted_receipt["oneOf"][0]["type"])
        self.assertEqual(
            {
                "PromotionReceipt.release_coordinate": "ReleaseCoordinate",
                "ReleaseCoordinate.hosted_automation_receipt": "GovernedLocator",
            },
            observed_types,
        )

    def test_graphql_binding_rejects_an_unbound_optional_authored_field(self) -> None:
        def remove_actor_organization(source: dict[str, Any]) -> None:
            del source["$defs"]["actor"]["properties"]["organization"]

        self.assert_graphql_source_mutation_rejected(
            remove_actor_organization,
            "GraphQL projection fields need directly mapped source properties:.*organization",
            source_document="schemas/common.schema.json",
            regenerate_ledger=True,
        )

    def test_graphql_binding_rejects_an_unbound_required_authored_field(self) -> None:
        def remove_accountable_role(source: dict[str, Any]) -> None:
            del source["properties"]["accountable_role"]
            source["required"].remove("accountable_role")

        self.assert_graphql_source_mutation_rejected(
            remove_accountable_role,
            "GraphQL projection fields need directly mapped source properties:.*accountable_role",
            regenerate_ledger=True,
        )

    def test_required_array_order_does_not_change_nullable_field_meaning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(
                ROOT / "schema-projections",
                root / "schema-projections",
            )
            source_path = root / schema_projections.SOURCE_SCHEMA_PATH
            source = json.loads(source_path.read_text(encoding="utf-8"))
            root_required = source["required"]
            root_required.insert(
                0,
                root_required.pop(root_required.index("release_coordinate")),
            )
            release_required = source["properties"]["release_coordinate"]["oneOf"][
                1
            ]["required"]
            release_required.insert(
                0,
                release_required.pop(
                    release_required.index("hosted_automation_receipt")
                ),
            )
            source_path.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            coverage_path = root / schema_projections.COVERAGE_SOURCE_PATH
            coverage_path.write_bytes(schema_projections.render_coverage_ledger(root))

            schema_projections.validate_coverage_ledger(root)
            schema_projections.validate_graphql_projection(root)

    def test_coverage_ledger_matches_the_exact_extracted_tuple_set(self) -> None:
        ledger = schema_projections.validate_coverage_ledger(ROOT)
        observed = {
            schema_projections._tuple_identity(record)
            for record in ledger["constraintTuples"]
        }
        expected = {
            (
                item.source_document,
                item.source_pointer,
                item.kind,
                item.value_sha256,
            )
            for item in schema_projections.extract_constraint_tuples(ROOT)
        }
        self.assertEqual(expected, observed)
        self.assertEqual(
            sorted({record[0] for record in observed}),
            ledger["source"]["reachableDocuments"],
        )
        self.assertEqual(
            (ROOT / schema_projections.COVERAGE_SOURCE_PATH).read_bytes(),
            schema_projections.render_coverage_ledger(ROOT),
        )

    def test_coverage_ledger_rejects_missing_duplicate_and_stale_records(self) -> None:
        original = schema_projections.load_json(
            ROOT / schema_projections.COVERAGE_SOURCE_PATH
        )
        missing = deepcopy(original)
        missing["constraintTuples"].pop()
        duplicate = deepcopy(original)
        duplicate["constraintTuples"].append(
            deepcopy(duplicate["constraintTuples"][0])
        )
        stale = deepcopy(original)
        stale["constraintTuples"][0]["disposition"] = "outside_projection"

        for name, candidate in (
            ("missing", missing),
            ("duplicate", duplicate),
            ("stale", stale),
        ):
            with self.subTest(name=name):
                with self.assertRaises(schema_projections.ProjectionError):
                    schema_projections.validate_coverage_ledger(
                        ROOT,
                        ledger=candidate,
                    )

    def test_source_constraint_change_requires_a_new_exact_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "schemas", root / "schemas")
            shutil.copytree(
                ROOT / "schema-projections",
                root / "schema-projections",
            )
            source_path = root / schema_projections.SOURCE_SCHEMA_PATH
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["properties"]["accountable_role"]["maxLength"] += 1
            source_path.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                schema_projections.ProjectionError,
                "tuple sets differ",
            ):
                schema_projections.validate_coverage_ledger(root)

    def test_graphql_shape_and_json_validation_keep_distinct_jobs(self) -> None:
        source = (ROOT / schema_projections.GRAPHQL_SOURCE_PATH).read_text(
            encoding="utf-8"
        )
        schema = build_ast_schema(parse(source))
        input_type = schema.get_type("PromotionReceiptInput")
        candidate = json.loads(
            (ROOT / "examples" / "promotion-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        candidate.update(
            {
                "assurance_stage": "verified",
                "evidence_mode": "observed",
                "promotion_state": "release_observed",
                "release_coordinate": None,
            }
        )

        errors: list[str] = []
        coerced = coerce_input_value(
            candidate,
            input_type,
            on_error=lambda path, value, error: errors.append(str(error)),
        )
        self.assertEqual([], errors)
        self.assertEqual(candidate, coerced)
        findings = validate_governance.SchemaValidator(
            ROOT / schema_projections.SOURCE_SCHEMA_PATH
        ).validate(candidate)
        self.assertTrue(findings)

    def test_candidate_and_observed_examples_validate_with_json_authority(self) -> None:
        validator = validate_governance.SchemaValidator(
            ROOT / schema_projections.SOURCE_SCHEMA_PATH
        )
        for path in (
            ROOT / "examples" / "promotion-receipt.json",
            ROOT / "promotion-receipt.json",
        ):
            with self.subTest(path=path.name):
                instance = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validator.validate(instance))

    def test_pages_projection_artifact_paths_and_bytes_are_closed(self) -> None:
        artifacts = schema_projections.projection_artifacts(ROOT)
        self.assertEqual(
            {
                schema_projections.COVERAGE_OUTPUT_PATH,
                schema_projections.GRAPHQL_OUTPUT_PATH,
                schema_projections.YAML_OUTPUT_PATH,
            },
            set(artifacts),
        )
        self.assertEqual(
            (ROOT / schema_projections.GRAPHQL_SOURCE_PATH).read_bytes(),
            artifacts[schema_projections.GRAPHQL_OUTPUT_PATH],
        )
        self.assertEqual(
            (ROOT / schema_projections.COVERAGE_SOURCE_PATH).read_bytes(),
            artifacts[schema_projections.COVERAGE_OUTPUT_PATH],
        )


if __name__ == "__main__":
    unittest.main()
