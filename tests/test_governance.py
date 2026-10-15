"""Regression tests for the governance package."""

from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
from hashlib import sha256
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
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


def run_git(repository: Path, *arguments: str) -> bytes:
    """Run Git in one isolated test repository and return exact output."""
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def commit_all(repository: Path, message: str) -> str:
    run_git(repository, "add", "--all")
    run_git(repository, "commit", "--no-gpg-sign", "-m", message)
    return run_git(repository, "rev-parse", "HEAD").decode("ascii").strip()


def release_observation(
    repository: Path,
    *,
    commit_oid: str,
    archive_digest: str,
) -> dict[str, object]:
    """Build one schema-valid observation from real Git object identifiers."""
    receipt = json.loads((ROOT / "promotion-receipt.json").read_text(encoding="utf-8"))
    tag = "governance-v2.2.0"
    tag_ref = f"refs/tags/{tag}"
    receipt["promotion_state"] = "release_observed"
    receipt["evidence_mode"] = "observed"
    receipt["assurance_stage"] = "verified"
    receipt["release_coordinate"] = {
        "git_object_format": run_git(
            repository, "rev-parse", "--show-object-format"
        ).decode("ascii").strip(),
        "tag": tag,
        "tag_object_oid": run_git(
            repository, "rev-parse", "--verify", tag_ref
        ).decode("ascii").strip(),
        "commit_oid": commit_oid,
        "archive_format": "git-tar",
        "archive_digest": archive_digest,
        "promoted_at": "2026-09-01T16:00:00Z",
        "local_proof_receipt": "governed://local/governance-proof/2.2.0",
        "hosted_check_contexts": [],
        "hosted_automation_receipt": None,
        "ruleset_receipt": "governed://github/rulesets/governance-2-2-0",
        "codeowner_resolution": "governed://github/codeowners/governance-2-2-0",
        "tag_signature_receipt": "governed://git/tag-signature/governance-2-2-0",
    }
    receipt["metadata"]["updated_at"] = "2026-09-01T16:05:00Z"
    return receipt


def initialize_release_repository(
    repository: Path,
    *,
    lightweight_tag: bool = False,
    carrier_from_base: bool = False,
) -> tuple[str, str]:
    """Create a tagged source and return its commit and archive digest."""
    run_git(repository, "init", "--initial-branch=main")
    run_git(repository, "config", "user.name", "Governance Test")
    run_git(repository, "config", "user.email", "governance-test@example.invalid")
    run_git(repository, "config", "commit.gpgSign", "false")
    run_git(repository, "config", "tag.gpgSign", "false")
    disabled_hooks = repository / ".git" / "test-disabled-hooks"
    disabled_hooks.mkdir()
    run_git(repository, "config", "core.hooksPath", str(disabled_hooks))
    (repository / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    commit_all(repository, "Create baseline")
    run_git(repository, "switch", "-c", "release")
    (repository / "accepted-source.txt").write_text(
        "accepted governance source\n", encoding="utf-8"
    )
    accepted_commit = commit_all(repository, "Prepare accepted source")
    if lightweight_tag:
        run_git(
            repository,
            "tag",
            "--no-sign",
            "governance-v2.2.0",
            accepted_commit,
        )
    else:
        run_git(
            repository,
            "tag",
            "--annotate",
            "--no-sign",
            "governance-v2.2.0",
            "--message",
            "Governance 2.2.0",
            accepted_commit,
        )
    archive = run_git(repository, "archive", "--format=tar", accepted_commit)
    if carrier_from_base:
        run_git(repository, "switch", "main")
    return accepted_commit, f"sha256:{sha256(archive).hexdigest()}"


def record_release_observation(repository: Path, receipt: dict[str, object]) -> str:
    (repository / "promotion-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return commit_all(repository, "Record release observation")


def load_database_examples() -> dict[str, object]:
    return {
        name: json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
        for name in validation.DATABASE_EXAMPLE_NAMES
    }


class GovernancePackageTests(unittest.TestCase):
    def test_schema_catalog_is_coherent(self) -> None:
        self.assertEqual([], validation.validate_schema_catalog())

    def test_readme_graph_has_registered_layers_and_resolving_routes(self) -> None:
        self.assertEqual([], validation.validate_readme_graph())

    def test_readme_fragment_ids_follow_stable_heading_labels(self) -> None:
        identifiers = validation._markdown_heading_ids(
            "# Site Reading Governance\n"
            "## Orientation records\n"
            "## Evidence and authority\n"
        )
        self.assertEqual(
            {"site-reading-governance", "orientation-records", "evidence-and-authority"},
            identifiers,
        )

    def test_readme_graph_requires_exact_unfenced_headings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            (temporary_root / "README.md").write_text(
                "# Fixture\n"
                "## Purposeful\n"
                "```markdown\n"
                "## Purpose\n"
                "```\n",
                encoding="utf-8",
            )
            with (
                patch.object(validation, "ROOT", temporary_root),
                patch.object(
                    validation,
                    "README_GRAPH_CONTRACTS",
                    {"README.md": ("## Purpose",)},
                ),
                patch.object(validation, "ROOT_ORIENTATION_SCHEMAS", {}),
            ):
                findings = validation.validate_readme_graph()

            self.assertTrue(
                any("requires '## Purpose'" in finding.message for finding in findings),
                findings,
            )

    def test_readme_graph_ignores_generated_cache_readmes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            (temporary_root / "README.md").write_text(
                "# Fixture\n\n## Purpose\n",
                encoding="utf-8",
            )
            cache = temporary_root / ".pytest_cache"
            cache.mkdir()
            (cache / "README.md").write_text("cache metadata\n", encoding="utf-8")
            with (
                patch.object(validation, "ROOT", temporary_root),
                patch.object(
                    validation,
                    "README_GRAPH_CONTRACTS",
                    {"README.md": ("## Purpose",)},
                ),
                patch.object(validation, "ROOT_ORIENTATION_SCHEMAS", {}),
            ):
                findings = validation.validate_readme_graph()

            self.assertEqual([], findings)

    def test_readme_graph_keeps_local_routes_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory) / "repository"
            temporary_root.mkdir()
            (temporary_root.parent / "outside.md").write_text(
                "# Outside\n",
                encoding="utf-8",
            )
            (temporary_root / "README.md").write_text(
                "# Fixture\n\n## Purpose\n\n[Outside](../outside.md#outside)\n",
                encoding="utf-8",
            )
            with (
                patch.object(validation, "ROOT", temporary_root),
                patch.object(
                    validation,
                    "README_GRAPH_CONTRACTS",
                    {"README.md": ("## Purpose",)},
                ),
                patch.object(validation, "ROOT_ORIENTATION_SCHEMAS", {}),
            ):
                findings = validation.validate_readme_graph()

            self.assertTrue(
                any("leaves the repository" in finding.message for finding in findings),
                findings,
            )

    def test_schema_catalog_diagnostic_names_stable_identifier_family(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            schema_dir = temporary_root / "schemas"
            schema_dir.mkdir()
            schema = json.loads(
                (ROOT / "schemas" / "common.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            schema["$id"] = (
                "https://schemas.driftframe.org/site-reading-governance/"
                "v2.1/common.schema.json"
            )
            (schema_dir / "common.schema.json").write_text(
                json.dumps(schema, indent=2) + "\n",
                encoding="utf-8",
            )

            with (
                patch.object(validation, "ROOT", temporary_root),
                patch.object(validation, "SCHEMA_DIR", schema_dir),
            ):
                findings = validation.validate_schema_catalog()

            self.assertTrue(
                any(
                    "stable /v2.0/ identifier family" in finding.message
                    for finding in findings
                ),
                findings,
            )

    def test_schema_catalog_rejects_unsupported_evaluator_keywords(self) -> None:
        findings = validation._validate_schema_keywords(
            {
                "type": "array",
                "contains": {"const": "required-item"},
            },
            "synthetic.schema.json",
        )
        self.assertTrue(
            any("contains" in finding.message for finding in findings),
            findings,
        )

    def test_every_mapped_example_validates(self) -> None:
        self.assertEqual([], validation.validate_examples())

    def test_root_orientation_records_form_one_coherent_control_surface(self) -> None:
        self.assertEqual([], validation.validate_repository_orientation())

    def test_historical_release_receipt_remains_separate_from_current_release(self) -> None:
        historical = json.loads(
            (
                ROOT
                / "release-receipts"
                / "governance-v2.1.0.json"
            ).read_text(encoding="utf-8")
        )
        current = json.loads(
            (ROOT / "promotion-receipt.json").read_text(encoding="utf-8")
        )

        self.assertEqual([], validation.validate_historical_release_receipts())
        self.assertEqual("RCP-GOVERNANCE-PROMOTION-002", historical["promotion_receipt_id"])
        self.assertEqual("release_observed", historical["promotion_state"])
        self.assertEqual("governance-v2.1.0", historical["release_coordinate"]["tag"])
        self.assertEqual(
            "8469c2a6b2c7f4445523cee262b961ffe3d2523b",
            historical["release_coordinate"]["commit_oid"],
        )
        self.assertEqual("RCP-GOVERNANCE-PROMOTION-003", current["promotion_receipt_id"])
        self.assertEqual("release_observed", current["promotion_state"])
        self.assertEqual(
            "governance-v2.2.0",
            current["release_coordinate"]["tag"],
        )

    def test_historical_release_receipt_rejects_whitespace_byte_drift(self) -> None:
        source = (
            ROOT
            / "release-receipts"
            / "governance-v2.1.0.json"
        ).read_bytes()
        with tempfile.TemporaryDirectory() as temporary_directory:
            receipt_directory = Path(temporary_directory)
            (receipt_directory / "governance-v2.1.0.json").write_bytes(
                source + b"\n"
            )
            with patch.object(
                validation,
                "RELEASE_RECEIPT_DIR",
                receipt_directory,
            ):
                findings = validation.validate_historical_release_receipts()

        self.assertTrue(
            any("whole-file SHA-256 identity" in finding.message for finding in findings),
            findings,
        )

    def test_candidate_provenance_requires_a_settling_promotion_item(self) -> None:
        records = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in validation.ROOT_ORIENTATION_SCHEMAS
        }
        node = records["machine-node.json"]
        first_receipt = records["first-receipt.json"]
        promotion = records["promotion-receipt.json"]
        horizon = records["coordination-horizon.json"]
        receipt_id = promotion["promotion_receipt_id"]

        node["lifecycle_state"] = "settling"
        node["current_provenance"] = {
            "release": "candidate-governance-v2.2.0",
            "commit": "0" * 40,
            "digest": "sha256:" + ("0" * 64),
        }
        node["open_receipts"] = [receipt_id]
        first_receipt["open_receipts"] = [receipt_id]
        promotion["promotion_state"] = "candidate_ready"
        promotion["evidence_mode"] = "planned"
        promotion["assurance_stage"] = "specified"
        promotion["release_coordinate"] = None
        promotion_item_id = "WORK-GOVERNANCE-PROMOTION-003"
        if promotion_item_id not in horizon["current_item_ids"]:
            horizon["current_item_ids"].append(promotion_item_id)
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

    def test_observed_release_closes_the_concrete_promotion_receipt(self) -> None:
        records = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in validation.ROOT_ORIENTATION_SCHEMAS
        }
        commit = "a" * 40
        digest = "sha256:" + ("b" * 64)
        node = records["machine-node.json"]
        first_receipt = records["first-receipt.json"]
        promotion = records["promotion-receipt.json"]
        horizon = records["coordination-horizon.json"]

        node["lifecycle_state"] = "active"
        node["current_provenance"] = {
            "release": "governance-v2.2.0",
            "commit": commit,
            "digest": digest,
        }
        node["open_receipts"] = []
        first_receipt["open_receipts"] = []
        promotion["promotion_state"] = "release_observed"
        promotion["evidence_mode"] = "observed"
        promotion["assurance_stage"] = "verified"
        promotion["release_coordinate"] = {
            "git_object_format": "sha1",
            "tag": "governance-v2.2.0",
            "tag_object_oid": "c" * 40,
            "commit_oid": commit,
            "archive_format": "git-tar",
            "archive_digest": digest,
            "promoted_at": "2026-07-28T22:00:00Z",
            "local_proof_receipt": "governed://local/governance-proof/2.2.0",
            "hosted_check_contexts": [],
            "hosted_automation_receipt": None,
            "ruleset_receipt": "governed://github/rulesets/governance-2-2-0",
            "codeowner_resolution": "governed://github/codeowners/governance-2-2-0",
            "tag_signature_receipt": "governed://git/tag-signature/governance-2-2-0",
        }
        items_by_id = {
            item["item_id"]: item for item in horizon["work_items"]
        }
        for item_id in (
            "WORK-MULTIFORMAT-PROJECTION-003",
            "WORK-DOWNSTREAM-REHEARSAL-003",
            "WORK-GOVERNANCE-PROMOTION-003",
        ):
            items_by_id[item_id]["state"] = "complete"

        self.assertEqual(
            [],
            validation.SchemaValidator(
                ROOT / "schemas" / "promotion-receipt.schema.json"
            ).validate(promotion),
        )
        self.assertEqual(
            [],
            validation._validate_repository_orientation_records(records),
        )

        items_by_id["WORK-DOWNSTREAM-REHEARSAL-003"]["state"] = "active"
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("promotion dependency closure" in finding.message for finding in findings),
            findings,
        )
        items_by_id["WORK-DOWNSTREAM-REHEARSAL-003"]["state"] = "complete"

        items_by_id["WORK-MULTIFORMAT-PROJECTION-003"]["state"] = "active"
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("promotion dependency closure" in finding.message for finding in findings),
            findings,
        )
        items_by_id["WORK-MULTIFORMAT-PROJECTION-003"]["state"] = "complete"

        promotion["release_coordinate"]["tag"] = "governance-v2.0.2"
        node["current_provenance"]["release"] = "governance-v2.0.2"
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("receipt target release" in finding.message for finding in findings),
            findings,
        )
        promotion["release_coordinate"]["tag"] = "governance-v2.2.0"
        node["current_provenance"]["release"] = "governance-v2.2.0"

        promotion["release_coordinate"]["hosted_check_contexts"] = [
            "governance-validation"
        ]
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("reviewed automation receipt" in finding.message for finding in findings),
            findings,
        )
        promotion["release_coordinate"]["hosted_automation_receipt"] = (
            "governed://github/actions/activation/governance-validation"
        )
        self.assertEqual(
            [],
            validation._validate_repository_orientation_records(records),
        )

    def test_hosted_promotion_context_requires_activation_receipt(self) -> None:
        promotion = json.loads(
            (ROOT / "promotion-receipt.json").read_text(encoding="utf-8")
        )
        promotion["promotion_state"] = "release_observed"
        promotion["evidence_mode"] = "observed"
        promotion["assurance_stage"] = "verified"
        promotion["release_coordinate"] = {
            "git_object_format": "sha1",
            "tag": "governance-v2.2.0",
            "tag_object_oid": "c" * 40,
            "commit_oid": "a" * 40,
            "archive_format": "git-tar",
            "archive_digest": "sha256:" + ("b" * 64),
            "promoted_at": "2026-07-28T22:00:00Z",
            "local_proof_receipt": "governed://local/governance-proof/2.2.0",
            "hosted_check_contexts": ["governance-validation"],
            "hosted_automation_receipt": None,
            "ruleset_receipt": "governed://github/rulesets/governance-2-2-0",
            "codeowner_resolution": "governed://github/codeowners/governance-2-2-0",
            "tag_signature_receipt": "governed://git/tag-signature/governance-2-2-0",
        }
        schema = validation.SchemaValidator(
            ROOT / "schemas" / "promotion-receipt.schema.json"
        )
        findings = schema.validate(promotion)
        self.assertTrue(
            any("oneOf branches" in finding.message for finding in findings),
            findings,
        )

        promotion["release_coordinate"]["hosted_automation_receipt"] = (
            "governed://github/actions/activation/governance-validation"
        )
        self.assertEqual([], schema.validate(promotion))

    def test_candidate_promotion_schema_keeps_release_coordinate_open(self) -> None:
        promotion = json.loads(
            (ROOT / "examples" / "promotion-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        promotion["release_coordinate"] = {
            "git_object_format": "sha1",
            "tag": "governance-v2.2.0",
            "tag_object_oid": "c" * 40,
            "commit_oid": "a" * 40,
            "archive_format": "git-tar",
            "archive_digest": "sha256:" + ("b" * 64),
            "promoted_at": "2026-07-28T22:00:00Z",
            "local_proof_receipt": "governed://local/governance-proof/2.2.0",
            "hosted_check_contexts": [],
            "hosted_automation_receipt": None,
            "ruleset_receipt": "governed://github/rulesets/governance-2-2-0",
            "codeowner_resolution": "governed://github/codeowners/governance-2-2-0",
            "tag_signature_receipt": "governed://git/tag-signature/governance-2-2-0",
        }
        findings = validation.SchemaValidator(
            ROOT / "schemas" / "promotion-receipt.schema.json"
        ).validate(promotion)
        self.assertTrue(
            any("type null" in finding.message for finding in findings),
            findings,
        )

    def test_release_verifier_observes_tag_archive_and_later_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(repository)
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            carrier_commit = record_release_observation(repository, receipt)

            self.assertNotEqual(
                receipt["release_coordinate"]["tag_object_oid"],
                accepted_commit,
            )
            self.assertNotEqual(carrier_commit, accepted_commit)
            self.assertEqual(
                [],
                validation.verify_release_coordinate(
                    repository, Path("promotion-receipt.json")
                ),
            )
            command = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "validate_governance.py"),
                    "--verify-release-coordinate",
                    "--release-repository",
                    str(repository),
                    "--promotion-receipt",
                    "promotion-receipt.json",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(0, command.returncode, command.stderr)
            self.assertEqual("Governance validation passed.\n", command.stdout)

    def test_release_verifier_binds_tag_to_target_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(repository)
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            receipt["target_release"] = "governance-v2.0.2"
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("target release" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_identifies_a_different_tag_subject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            initialize_release_repository(repository)
            (repository / "later-source.txt").write_text(
                "different source\n", encoding="utf-8"
            )
            different_commit = commit_all(repository, "Create different source")
            different_archive = run_git(
                repository, "archive", "--format=tar", different_commit
            )
            receipt = release_observation(
                repository,
                commit_oid=different_commit,
                archive_digest=f"sha256:{sha256(different_archive).hexdigest()}",
            )
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("annotated tag subject" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_identifies_a_different_tag_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(repository)
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            receipt["release_coordinate"]["tag_object_oid"] = accepted_commit
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("annotated tag" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_identifies_a_different_archive_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, _ = initialize_release_repository(repository)
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest="sha256:" + ("d" * 64),
            )
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("git archive --format=tar" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_requires_an_annotated_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(
                repository, lightweight_tag=True
            )
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("annotated tag object" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_requires_subject_ancestry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(
                repository, carrier_from_base=True
            )
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            record_release_observation(repository, receipt)

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("ancestor of the receipt carrier" in item.message for item in findings),
                findings,
            )

    def test_release_verifier_binds_receipt_bytes_to_the_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            accepted_commit, archive_digest = initialize_release_repository(repository)
            receipt = release_observation(
                repository,
                commit_oid=accepted_commit,
                archive_digest=archive_digest,
            )
            record_release_observation(repository, receipt)
            receipt["metadata"]["updated_at"] = "2026-09-01T16:06:00Z"
            (repository / "promotion-receipt.json").write_text(
                json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
            )

            findings = validation.verify_release_coordinate(
                repository, Path("promotion-receipt.json")
            )
            self.assertTrue(
                any("working receipt bytes" in item.message for item in findings),
                findings,
            )

    def test_root_contract_digest_binds_material_contract_file(self) -> None:
        cases = (
            (0, "schemas/simulated-receipt-closure.schema.json"),
            (1, "tools/check_branch_flow.py"),
        )
        for index, expected_material in cases:
            with self.subTest(contract=index):
                records = {
                    name: json.loads((ROOT / name).read_text(encoding="utf-8"))
                    for name in validation.ROOT_ORIENTATION_SCHEMAS
                }
                records["machine-node.json"]["contracts"][index]["digest"] = (
                    "sha256:" + ("f" * 64)
                )
                records["first-receipt.json"]["contract_state"] = records[
                    "machine-node.json"
                ]["contracts"]
                findings = validation._validate_repository_orientation_records(records)
                self.assertTrue(
                    any(
                        finding.path
                        == f"machine-node.json.contracts[{index}].digest"
                        and expected_material in finding.message
                        for finding in findings
                    ),
                    findings,
                )

    def test_ruleset_exports_preserve_governed_flow(self) -> None:
        self.assertEqual([], validation.validate_rulesets())

    def test_main_promotion_ruleset_preserves_one_review_bundle(self) -> None:
        expected = {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews_on_push": True,
            "require_code_owner_review": True,
            "require_last_push_approval": True,
            "required_review_thread_resolution": True,
            "allowed_merge_methods": ["merge", "squash"],
        }
        ruleset_paths = sorted(path.name for path in (ROOT / "rulesets").glob("*.json"))
        self.assertEqual(["main.json", "release-tags.json"], ruleset_paths)
        ruleset = json.loads(
            (ROOT / "rulesets" / "main.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            ["refs/heads/main"],
            ruleset["conditions"]["ref_name"]["include"],
        )
        pull_request = next(
            rule for rule in ruleset["rules"] if rule["type"] == "pull_request"
        )
        self.assertEqual(expected, pull_request["parameters"])
        branching = (ROOT / "BRANCHING.md").read_text(encoding="utf-8")
        self.assertIn("`develop` is the lean\nintegration branch", branching)
        self.assertIn("Remove the short-lived release branch", branching)

    def test_repository_attribution_uses_its_source_local_carrier(self) -> None:
        authors = (ROOT / "AUTHORS").read_text(encoding="utf-8")
        self.assertTrue(authors.startswith("# General provenance\n"))
        self.assertIn("Driftframe Studios, Limited Liability Company", authors)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[`AUTHORS`](AUTHORS)", readme)
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        self.assertIn("/AUTHORS @driftframestudios", codeowners)
        self.assertIn("/.github/dependabot.yml @driftframestudios", codeowners)
        self.assertNotIn("dependabot.manual.yml", codeowners)

    def test_public_ready_skill_has_one_exact_identity_and_path(self) -> None:
        self.assertEqual([], validation.validate_public_ready_skills())
        skill_path = ROOT / validation.PUBLIC_SKILL_SOURCE_PATH
        metadata, content = validation.parse_skill_source(skill_path)
        self.assertEqual(validation.PUBLIC_SKILL_METADATA, metadata)
        self.assertEqual(
            "governance-schema-release-lineage",
            metadata["name"],
        )
        self.assertIn("authorized resolver", " ".join(content.split()))
        self.assertNotIn("https://github.com/", content)
        self.assertIsNone(validation.HTML_LINE_BREAK.search(content))

    def test_public_possible_skill_workbench_has_copy_local_lineage(self) -> None:
        self.assertEqual([], validation.validate_public_possible_skills())
        for relative, expected in validation.PUBLIC_POSSIBLE_SKILL_METADATA.items():
            metadata, content = validation.parse_skill_source(ROOT / relative)
            for key, value in expected.items():
                self.assertEqual(value, metadata[key])
            self.assertEqual(Path(relative).parent.name, metadata["name"])
            self.assertIn("independently usable", " ".join(content.split()))

    def test_public_possible_lineage_drift_is_visible(self) -> None:
        relative = ".agents/skills/repository-reentry/SKILL.md"
        expected = validation.PUBLIC_POSSIBLE_SKILL_METADATA[relative]
        with patch.dict(expected, {"upstream_revision": "0" * 40}):
            findings = validation.validate_public_possible_skills()
        self.assertTrue(
            any(
                "upstream source coordinates" in finding.message
                for finding in findings
            ),
            findings,
        )

    def test_public_language_route_is_complete_and_locator_safe(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "NEGATION_AWARE_LANGUAGE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "[`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md)",
            readme,
        )
        self.assertIn("public authority", guide)
        self.assertNotIn("app.notion", readme.lower())
        self.assertNotIn("app.notion", guide.lower())

    def test_workflows_use_bounded_permissions_and_immutable_actions(self) -> None:
        self.assertEqual([], validation.validate_workflows())

    def test_vale_author_feedback_is_pinned_advisory_and_human_cued(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        author_job = workflow.split("  author-feedback:", 1)[1].split(
            "\n  governance-validation:",
            1,
        )[0]
        governance_job = workflow.split("\n  governance-validation:", 1)[1]
        self.assertIn(
            "if: ${{ vars.ENABLE_GITHUB_ACTIONS == 'true' && inputs.confirm_run }}",
            author_job,
        )
        self.assertIn("continue-on-error: true", author_job)
        self.assertIn(
            "VALE_ARCHIVE: vale_3.15.2_Linux_64-bit.tar.gz",
            author_job,
        )
        self.assertIn(
            "fc72e64454d6bd7af91905d4faebbf411bae3eec17bb572f4101311212bc0d9e",
            author_job,
        )
        self.assertIn(
            "https://github.com/vale-cli/vale/releases/download/"
            "v3.15.2/$VALE_ARCHIVE",
            author_job,
        )
        self.assertIn("sha256sum --check --strict", author_job)
        self.assertIn("--config=.vale.ini --no-global --no-exit", author_job)
        self.assertIn("--minAlertLevel=warning .", author_job)
        self.assertNotIn("vale", governance_job.lower())
        self.assertNotIn("author-feedback", governance_job)
        self.assertNotIn("needs:", author_job)
        self.assertNotIn("vale-action", workflow.lower())
        self.assertNotIn("reviewdog", workflow.lower())

        configuration = (ROOT / ".vale.ini").read_text(encoding="utf-8")
        documentation = (
            ROOT / "docs" / "AUTHOR_FEEDBACK.md"
        ).read_text(encoding="utf-8")
        self.assertIn("MinAlertLevel = suggestion", configuration)
        self.assertIn(
            "default includes both warnings and suggestions",
            documentation,
        )
        self.assertIn("CI requests `--minAlertLevel=warning`", documentation)
        self.assertIn(
            "vale --config=.vale.ini --no-global .",
            documentation,
        )

    def test_release_branch_advances_main(self) -> None:
        self.assertEqual([], branch_flow.check_flow("main", "release/2.1.0"))

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
        self.assertTrue(branch_flow.check_flow("main", "release/v2.1.0"))

    def test_schema_release_coordinates_are_current(self) -> None:
        self.assertEqual("2.2.0", (ROOT / "VERSION").read_text().strip())
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
        machine_node = json.loads(
            (ROOT / "examples" / "machine-node.json").read_text()
        )
        self.assertEqual(
            validation.SCHEMA_RELEASE,
            machine_node["schema_release"],
        )

    def test_accepted_2_1_machine_node_remains_schema_compatible(self) -> None:
        accepted = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "machine-node-v2.1.0.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            [],
            validation.SchemaValidator(
                ROOT / "schemas" / "machine-node.schema.json"
            ).validate(accepted),
        )

    def test_root_machine_node_selects_current_schema_release(self) -> None:
        records = {
            name: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for name in validation.ROOT_ORIENTATION_SCHEMAS
        }
        records["machine-node.json"]["schema_release"] = "2.1.0"
        findings = validation._validate_repository_orientation_records(records)
        self.assertTrue(
            any("root orientation must select" in finding.message for finding in findings),
            findings,
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

    def test_exact_decimal_contract_requires_precision_scale_and_unit(self) -> None:
        schema = ROOT / "schemas" / "data-contract.schema.json"
        document = json.loads((ROOT / "examples" / "data-contract.json").read_text())
        field = document["entities"][1]["fields"][2]
        for required_field in ("precision", "scale", "unit"):
            candidate = json.loads(json.dumps(document))
            candidate["entities"][1]["fields"][2].pop(required_field)
            findings = validation.SchemaValidator(schema).validate(candidate)
            self.assertTrue(
                any(required_field in item.message for item in findings),
                (required_field, findings),
            )
        self.assertEqual("exact_decimal", field["semantic_type"])

    def test_data_contract_accepts_bounded_migration_history_relations(self) -> None:
        schema = ROOT / "schemas" / "data-contract.schema.json"
        document = json.loads((ROOT / "examples" / "data-contract.json").read_text())
        for relation in ("flyway_schema_history", "public.flyway_schema_history"):
            with self.subTest(relation=relation):
                candidate = json.loads(json.dumps(document))
                candidate["database"]["migration_history_table"] = relation
                self.assertEqual([], validation.SchemaValidator(schema).validate(candidate))

        for relation in (
            "catalog.public.flyway_schema_history",
            "Public.flyway_schema_history",
            "public.flyway_schema_history;drop",
        ):
            with self.subTest(rejected_relation=relation):
                candidate = json.loads(json.dumps(document))
                candidate["database"]["migration_history_table"] = relation
                findings = validation.SchemaValidator(schema).validate(candidate)
                self.assertTrue(any("pattern" in item.message for item in findings))

    def test_database_contracts_reject_unreviewed_properties(self) -> None:
        mapping = {
            "data-contract.json": "data-contract.schema.json",
            "database-refactor-finding.json": "database-refactor-finding.schema.json",
            "database-migration-plan.json": "database-migration-plan.schema.json",
            "database-migration-receipt.json": "database-migration-receipt.schema.json",
            "data-reconciliation.json": "data-reconciliation.schema.json",
            "database-release-manifest.json": "database-release-manifest.schema.json",
        }
        for document_name, schema_name in mapping.items():
            with self.subTest(document=document_name):
                document = json.loads(
                    (ROOT / "examples" / document_name).read_text(encoding="utf-8")
                )
                document["unreviewed_property"] = True
                findings = validation.SchemaValidator(
                    ROOT / "schemas" / schema_name
                ).validate(document)
                self.assertTrue(
                    any("outside the contract" in item.message for item in findings),
                    findings,
                )

    def _validate_changed_examples(self, changed):
        original_load = validation.load_json

        def load(path):
            if Path(path).parent == validation.EXAMPLE_DIR and Path(path).name in changed:
                return changed[Path(path).name]
            return original_load(path)

        with patch.object(validation, "load_json", side_effect=load):
            return validation.validate_examples()

    def test_example_admission_preserves_structural_findings_and_report(self) -> None:
        cases = (
            ("data-contract.json", "entities", None, ".entities"),
            ("database-migration-plan.json", "phase_sequence", None, ".phase_sequence"),
            ("data-reconciliation.json", "criteria", None, ".criteria"),
            ("data-contract.json", None, [], ""),
            ("data-contract.json", "database", None, ".database"),
            ("data-contract.json", "entities", [None], ".entities[0]"),
            ("database-migration-plan.json", "phase_sequence", [None], ".phase_sequence[0]"),
            ("data-reconciliation.json", "criteria", [None], ".criteria[0]"),
        )
        for name, field, value, suffix in cases:
            with self.subTest(document=name, field=field, value=value):
                record = validation.load_json(validation.EXAMPLE_DIR / name)
                if field is None:
                    record = value
                else:
                    record[field] = value
                before = deepcopy(record)
                findings = self._validate_changed_examples({name: record})
                self.assertTrue(any(
                    item.path == f"examples/{name}{suffix}" and "must have type" in item.message
                    for item in findings
                ), findings)
                self.assertEqual(record, before)
                output = io.StringIO()
                with redirect_stdout(output):
                    status = validation.report(findings)
                self.assertEqual(status, 1)
                self.assertIn(f"examples/{name}{suffix}", output.getvalue())
                self.assertEqual(findings, self._validate_changed_examples({name: record}))

    def test_example_cli_reports_malformed_record_with_independent_findings(self) -> None:
        records = load_database_examples()
        records["database-migration-plan.json"]["phase_sequence"] = None
        records["data-contract.json"]["entities"][1]["constraints"][0]["referenced_entity_id"] = "ENTITY-UNKNOWN-001"
        comparison = validation.load_json(validation.EXAMPLE_DIR / "comparison.json")
        comparison["summary"]["total"] += 1
        records["comparison.json"] = comparison
        original_load = validation.load_json

        def load(path):
            if Path(path).parent == validation.EXAMPLE_DIR and Path(path).name in records:
                return records[Path(path).name]
            return original_load(path)

        output = io.StringIO()
        with patch.object(validation, "load_json", side_effect=load), patch.object(sys, "argv", ["validate_governance.py"]), redirect_stdout(output):
            status = validation.main([])
        self.assertEqual(status, 1)
        self.assertIn("phase_sequence: value must have type array", output.getvalue())
        self.assertIn("foreign-key target entity must resolve", output.getvalue())
        self.assertIn("summary total must equal result count", output.getvalue())

    def test_each_example_family_requires_structural_admission(self) -> None:
        mapping = validation.load_json(validation.EXAMPLE_DIR / "example-map.json")["schema_map"]
        for name in mapping:
            with self.subTest(document=name):
                findings = self._validate_changed_examples({name: None})
                self.assertEqual(len(findings), 1, findings)
                self.assertEqual(findings[0].path, f"examples/{name}")
                self.assertIn("must have type object", findings[0].message)

    def test_admitted_database_faults_retain_cumulative_semantic_findings(self) -> None:
        records = load_database_examples()
        records["data-contract.json"]["entities"][1]["constraints"][0]["referenced_entity_id"] = "ENTITY-UNKNOWN-001"
        records["database-migration-plan.json"]["phase_sequence"][0]["dependency_phase_ids"] = ["PHASE-CONTRACT-001"]
        records["data-reconciliation.json"]["criteria"][1]["outcome"] = "failed"
        records["database-release-manifest.json"]["data_contract"]["digest"] = "sha256:" + "0" * 64
        before = deepcopy(records)
        for name, record in records.items():
            self.assertEqual([], validation.SchemaValidator(
                validation.SCHEMA_DIR / name.replace(".json", ".schema.json")
            ).validate(record))
        findings = self._validate_changed_examples(records)
        messages = [item.message for item in findings]
        for message in (
            "foreign-key target entity must resolve",
            "each phase dependency must precede its dependent phase",
            "passing reconciliation requires a passing result for every criterion",
            "release manifest data-contract coordinate must match the contract example",
        ):
            self.assertIn(message, messages)
        self.assertEqual(records, before)

    def test_database_identity_ambiguity_preserves_local_findings(self) -> None:
        records = load_database_examples()
        contract = records["data-contract.json"]
        duplicate = deepcopy(contract["entities"][0])
        duplicate["fields"] = [duplicate["fields"][1]]
        duplicate["primary_key_field_ids"] = [duplicate["fields"][0]["field_id"]]
        contract["entities"].append(duplicate)
        contract["entities"][0]["fields"][1]["physical_type"] = "text"
        plan = records["database-migration-plan.json"]
        repeated_phase = deepcopy(plan["phase_sequence"][0])
        repeated_phase["sequence"] = 99
        plan["phase_sequence"].append(repeated_phase)
        findings = self._validate_changed_examples(records)
        messages = [item.message for item in findings]
        self.assertIn("entity identifiers must be unique", messages)
        self.assertIn("migration phase identifiers must be unique", messages)
        self.assertIn("PostgreSQL instant fields use timestamptz", messages)
        # Ambiguous targets retain their duplicate finding; neither duplicate wins lookup.
        self.assertNotIn("every foreign-key target field must resolve", messages)
        self.assertNotIn("each phase dependency must precede its dependent phase", messages)

    def test_database_contract_resolves_native_primitives_and_foreign_keys(
        self,
    ) -> None:
        records = load_database_examples()
        contract = records["data-contract.json"]
        contract["entities"][0]["fields"][1]["physical_type"] = "text"
        contract["entities"][1]["constraints"][0]["referenced_field_ids"] = [
            "FIELD-UNKNOWN-001"
        ]
        findings = validation._validate_database_examples(records)
        messages = " ".join(item.message for item in findings)
        self.assertIn("PostgreSQL instant fields use timestamptz", messages)
        self.assertIn("foreign-key target field must resolve", messages)

    def test_database_contract_requires_coherent_key_and_decimal_declarations(self) -> None:
        def unequal_arity(entities):
            entities[1]["constraints"][0]["field_ids"].append("FIELD-RESULT-ID-001")

        def nonunique_target(entities):
            field = dict(entities[0]["fields"][0])
            field.update(field_id="FIELD-SPECIMEN-OTHER-001", column_name="other_id")
            entities[0]["fields"].append(field)
            entities[1]["constraints"][0]["referenced_field_ids"] = [field["field_id"]]

        def nullable_primary(entities):
            entities[0]["fields"][0]["nullable"] = True

        def decimal_disagreement(entities):
            entities[1]["fields"][2]["physical_type"] = "numeric(6,2)"

        for mutate, expected_path, expected_message in (
            (unequal_arity, "constraints[0].referenced_field_ids", "equal column counts"),
            (nonunique_target, "constraints[0].referenced_field_ids", "primary or unique key"),
            (nullable_primary, "fields[0].nullable", "nonnullable"),
            (decimal_disagreement, "fields[2].physical_type", "precision and scale"),
        ):
            with self.subTest(case=mutate.__name__):
                records = load_database_examples()
                mutate(records["data-contract.json"]["entities"])
                self.assertEqual([], validation.SchemaValidator(
                    ROOT / "schemas" / "data-contract.schema.json"
                ).validate(records["data-contract.json"]))
                findings = validation._validate_database_examples(records)
                self.assertTrue(any(
                    expected_path in item.path and expected_message in item.message
                    for item in findings
                ), findings)

    def test_database_contract_accepts_composite_unique_and_self_references(self) -> None:
        for key_kind in ("primary", "unique"):
            with self.subTest(key_kind=key_kind):
                records = load_database_examples()
                parent, child = records["data-contract.json"]["entities"]
                extra = dict(parent["fields"][0])
                extra.update(field_id="FIELD-SPECIMEN-OTHER-001", column_name="other_id")
                parent["fields"].append(extra)
                target_ids = [parent["fields"][0]["field_id"], extra["field_id"]]
                if key_kind == "primary":
                    parent["primary_key_field_ids"] = target_ids
                else:
                    parent["constraints"].append({
                        "constraint_id": "CONSTRAINT-SPECIMEN-UNIQUE-001",
                        "constraint_type": "unique", "field_ids": target_ids,
                        "validation_state": "validated",
                    })
                child["constraints"][0]["field_ids"].append("FIELD-RESULT-ID-001")
                child["constraints"][0]["referenced_field_ids"] = target_ids[::-1]
                parent["constraints"].append({
                    "constraint_id": "CONSTRAINT-SPECIMEN-SELF-001",
                    "constraint_type": "foreign_key", "field_ids": target_ids,
                    "referenced_entity_id": parent["entity_id"],
                    "referenced_field_ids": target_ids, "validation_state": "validated",
                })
                child["fields"][2]["physical_type"] = "decimal(18,6)"
                self.assertEqual([], validation.SchemaValidator(
                    ROOT / "schemas" / "data-contract.schema.json"
                ).validate(records["data-contract.json"]))
                self.assertEqual([], validation._validate_database_examples(records))

    def test_migration_receipt_binds_phase_identity_to_its_sequence(self) -> None:
        records = load_database_examples()
        phases = records["database-migration-receipt.json"]["phase_results"]
        phases[0]["phase_id"], phases[1]["phase_id"] = phases[1]["phase_id"], phases[0]["phase_id"]
        findings = validation._validate_database_examples(records)
        self.assertTrue(any(
            item.path == "examples/database-migration-receipt.json.phase_results"
            and "phase order must match" in item.message
            for item in findings
        ), findings)

    def test_database_numeric_diagnostics_preserve_structural_failure_reporting(self) -> None:
        records = load_database_examples()
        field = records["data-contract.json"]["entities"][1]["fields"][2]
        field["physical_type"] = "numeric(" + "9" * 4400 + ",6)"
        structural = validation.SchemaValidator(
            ROOT / "schemas" / "data-contract.schema.json"
        ).validate(records["data-contract.json"])
        self.assertTrue(any("maxLength" in item.message for item in structural))
        findings = validation._validate_database_examples(records)
        self.assertTrue(any("precision and scale" in item.message for item in findings))
        field["physical_type"] = "numeric(18,006)"
        self.assertEqual([], validation._validate_database_examples(records))

    def test_destructive_migration_requires_scoped_approval(self) -> None:
        schema = ROOT / "schemas" / "database-migration-plan.schema.json"
        document = json.loads(
            (ROOT / "examples" / "database-migration-plan.json").read_text()
        )
        document["approval_ids"] = []
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("minItems" in item.message for item in findings),
            findings,
        )

    def test_writer_coordination_assigns_mechanics_to_a_governed_owner(
        self,
    ) -> None:
        schema = ROOT / "schemas" / "database-migration-plan.schema.json"
        document = json.loads(
            (ROOT / "examples" / "database-migration-plan.json").read_text()
        )
        document["execution_policy"]["writer_coordination"]["owner"] = (
            "caller_owned_advisory_lock"
        )
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("outside the enum" in item.message for item in findings),
            findings,
        )

    def test_migration_phase_dependencies_are_ordered_and_acyclic(self) -> None:
        records = load_database_examples()
        plan = records["database-migration-plan.json"]
        plan["phase_sequence"][0]["dependency_phase_ids"] = [
            "PHASE-CONTRACT-001"
        ]
        findings = validation._validate_database_examples(records)
        self.assertTrue(
            any("must precede" in item.message for item in findings),
            findings,
        )

    def test_migration_receipt_binds_plan_digests_and_complete_phases(self) -> None:
        records = load_database_examples()
        receipt = records["database-migration-receipt.json"]
        receipt["target_schema_digest"] = "sha256:" + ("0" * 64)
        receipt["phase_results"].pop()
        findings = validation._validate_database_examples(records)
        messages = " ".join(item.message for item in findings)
        self.assertIn("must match the migration plan", messages)
        self.assertIn("cover every planned phase exactly once", messages)

    def test_migration_receipt_preserves_planned_lock_budget(self) -> None:
        records = load_database_examples()
        records["database-migration-receipt.json"]["execution_metrics"][
            "maximum_lock_held_milliseconds"
        ] = 1001
        findings = validation._validate_database_examples(records)
        self.assertTrue(
            any("planned phase budget" in item.message for item in findings),
            findings,
        )

    def test_passing_migration_and_reconciliation_require_passing_components(
        self,
    ) -> None:
        records = load_database_examples()
        records["database-migration-receipt.json"]["phase_results"][1][
            "outcome"
        ] = "failed"
        records["data-reconciliation.json"]["criteria"][1]["outcome"] = "failed"
        findings = validation._validate_database_examples(records)
        messages = " ".join(item.message for item in findings)
        self.assertIn("passing result for every phase", messages)
        self.assertIn("passing result for every criterion", messages)

    def test_release_manifest_binds_contract_receipts_acceptance_and_findings(
        self,
    ) -> None:
        records = load_database_examples()
        manifest = records["database-release-manifest.json"]
        manifest["data_contract"]["digest"] = "sha256:" + ("0" * 64)
        manifest["required_receipt_ids"] = []
        manifest["acceptance_bindings"].pop()
        manifest["unresolved_finding_ids"] = []
        findings = validation._validate_database_examples(records)
        messages = " ".join(item.message for item in findings)
        self.assertIn("data-contract coordinate", messages)
        self.assertIn("require the migration receipt", messages)
        self.assertIn("represent Scientific, Quality, Regulatory, Security", messages)
        self.assertIn("must remain visible", messages)

    def test_release_manifest_requires_contiguous_convergent_migrations(self) -> None:
        records = load_database_examples()
        manifest = records["database-release-manifest.json"]
        manifest["ordered_migrations"][0]["sequence"] = 2
        manifest["supported_upgrade_baselines"][0]["schema_digest"] = (
            "sha256:" + ("0" * 64)
        )
        manifest["current_schema_digest"] = "sha256:" + ("1" * 64)
        findings = validation._validate_database_examples(records)
        messages = " ".join(item.message for item in findings)
        self.assertIn("contiguous ordered chain", messages)
        self.assertIn("convergence receipt", messages)
        self.assertIn("final applied migration schema", messages)

    def test_migration_evidence_instants_use_canonical_utc_interchange(self) -> None:
        schema = ROOT / "schemas" / "database-migration-receipt.schema.json"
        document = json.loads(
            (ROOT / "examples" / "database-migration-receipt.json").read_text()
        )
        document["performed_at"] = "2026-08-04T11:00:12-04:00"
        findings = validation.SchemaValidator(schema).validate(document)
        self.assertTrue(
            any("pattern" in item.message for item in findings),
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

    def test_high_consequence_language_control_requires_complete_operational_fields(
        self,
    ) -> None:
        schema = ROOT / "schemas" / "language-control.schema.json"
        document = json.loads(
            (ROOT / "examples" / "language-control.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual([], validation.SchemaValidator(schema).validate(document))
        for field in (
            "target_state",
            "boundary",
            "replacement_behavior",
            "verification",
            "owner_role",
            "evidence",
        ):
            with self.subTest(field=field):
                candidate = json.loads(json.dumps(document))
                candidate.pop(field)
                findings = validation.SchemaValidator(schema).validate(candidate)
                self.assertTrue(
                    any(field in finding.message for finding in findings),
                    findings,
                )

    def test_language_check_passes_repository(self) -> None:
        result = language.scan_repository(ROOT)
        self.assertEqual((), result.findings)


if __name__ == "__main__":
    unittest.main()
