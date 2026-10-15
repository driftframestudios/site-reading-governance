"""Governance-authored lifecycle counterexamples and expected assurance claims."""
from __future__ import annotations

import contextlib
from dataclasses import FrozenInstanceError
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from assurance_companion import AssuranceError, digest, encoded, read_regular
import lifecycle_assurance as receiver


def available():
    return (importlib.util.find_spec("lims_eln_contracts") is not None
            and importlib.util.find_spec("lims_eln_contracts.database_lifecycle") is not None)


def profile(disposition="disposable", initial="absent"):
    """Choose one independently authored Governance review subject."""
    operator = "ref:governance-review-operator"
    owner = "ref:external-database-owner" if disposition == "external" else operator
    policy, credential = {
        "disposable": ("current_invocation_owned", "invocation_runtime"),
        "retained": ("explicit_owner_decision", "operator_runtime"),
        "external": ("external_owner_only", "external_owner_runtime"),
    }[disposition]
    return {
        "schema_ref": "urn:driftframe:lims-eln:database-lifecycle-profile:1.0.0",
        "schema_version": "1.0.0",
        "source": {"source_ref": "ref:program-database-lifecycle", "revision": receiver.SOURCE["revision"]},
        "profile_ref": "ref:governance-recovery-review",
        "evidence_class": "authored_example",
        "invocation": {"invocation_ref": "ref:governance-review-session", "owner_ref": operator},
        "requested_profile": {
            "disposition": disposition, "engine": "postgresql", "engine_major": 17,
            "migration_ref": "ref:reviewed-migration-sequence",
            "credential_receiver_class": credential,
            "permitted_actions": ["create", "migrate", "restore", "cleanup", "inspect", "stop"],
            "cleanup_policy": policy, "recovery_ref": "ref:resource-owner-recovery",
        },
        "resource": {
            "resource_ref": "ref:governance-review-database", "owner_ref": owner,
            "creation_owner_ref": owner,
            "created_by_invocation_ref": "ref:governance-review-session" if disposition == "disposable" else None,
            "initial_state": initial, "state": initial,
        },
        "composition": {"state": "not_observed", "capability_ref": None, "capability_digest": None},
        "readiness": {"state": "not_observed", "observation_ref": None},
        "operations": [], "unresolved_resource_refs": [],
    }


def event(subject, name, action, before, after, outcome="succeeded", *, actor=None):
    return {
        "operation_ref": "ref:" + name, "action": action,
        "from_state": before, "to_state": after, "outcome": outcome,
        "authority": {
            "owner_ref": subject["resource"]["owner_ref"],
            "actor_ref": actor or subject["invocation"]["owner_ref"],
            "decision_ref": "ref:reviewed-owner-decision",
            "basis": "invocation_owned" if subject["requested_profile"]["disposition"] == "disposable" else "explicit_owner_decision",
            "destructive_authorized": action in {"restore", "cleanup"},
        },
        "compatibility": {"state": "not_observed", "engine_major": None, "migration_ref": None, "observation_ref": None},
        "evidence_ref": None if outcome == "requested" else "ref:" + name + "-evidence",
        "failure_code": action + "_failed" if outcome == "failed" else "resource_unresolved" if outcome == "unresolved" else None,
    }


def timeline(subject, *events):
    subject["operations"] = list(events)
    subject["resource"]["state"] = events[-1]["to_state"] if events else subject["resource"]["initial_state"]
    subject["unresolved_resource_refs"] = ([subject["resource"]["resource_ref"]]
                                            if subject["resource"]["state"] == "unresolved" else [])
    return subject


class LifecycleBoundaryTests(unittest.TestCase):
    def test_regular_file_budget_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "input.json"
            path.write_bytes(b"12345")
            self.assertEqual(read_regular(path, max_bytes=5), b"12345")
            with self.assertRaises(AssuranceError) as caught:
                read_regular(path, max_bytes=4)
            self.assertEqual(caught.exception.code, "input_size")
            alias = path.with_name("alias.json")
            alias.symlink_to(path)
            with self.assertRaises(AssuranceError) as caught:
                read_regular(alias, max_bytes=5)
            self.assertEqual(caught.exception.code, "input_file")
            for budget in (-1, True, 4 * 1024 * 1024 + 1):
                with self.assertRaises(ValueError):
                    read_regular(path, max_bytes=budget)

    def test_missing_optional_owner_has_install_route(self):
        failure = ModuleNotFoundError(name="lims_eln_contracts.database_lifecycle")
        with patch.object(receiver, "import_module", side_effect=failure):
            with self.assertRaises(AssuranceError) as caught:
                receiver.receive_lifecycle(b"{}")
        self.assertEqual(caught.exception.code, "lifecycle_dependency")

    def test_nested_dependency_breakage_remains_visible(self):
        failure = ModuleNotFoundError(name="unexpected_dependency")
        with patch.object(receiver, "import_module", side_effect=failure):
            with self.assertRaises(ModuleNotFoundError) as caught:
                receiver.receive_lifecycle(b"{}")
        self.assertIs(caught.exception, failure)


@unittest.skipUnless(available(), "Install requirements-lifecycle.txt for Program lifecycle admission.")
class LifecycleAssuranceTests(unittest.TestCase):
    def receive(self, subject, capability=None):
        return receiver.receive_lifecycle(encoded(subject), capability_payload=capability).to_document()

    def rejects(self, subject, code, capability=None):
        with self.assertRaises(AssuranceError) as caught:
            self.receive(subject, capability)
        self.assertEqual(caught.exception.code, code)

    def test_published_example_retains_failed_cleanup_for_next_owner(self):
        payload = (ROOT / "examples/database-lifecycle-assurance.json").read_bytes()
        result = receiver.receive_lifecycle(payload).to_document()
        self.assertEqual(result["resource"]["state"], "unresolved")
        self.assertEqual(result["operation_outcomes"], {"requested": 0, "succeeded": 1, "failed": 1, "unresolved": 0})
        self.assertEqual(result["unresolved_resource_refs"], ["ref:governance-review-database"])
        self.assertEqual(result["requested_profile"]["recovery_ref"], "ref:resource-owner-recovery")

    def test_byte_budget_and_strict_json_are_enforced_at_api_boundary(self):
        for payload, code in ((b" " * (receiver.MAX_BYTES + 1), "input_bytes"),
                              ("{}", "input_bytes"), (b"\xff", "utf8"),
                              (b'{"x":NaN}', "json_number"),
                              (b"[]", "contract_shape")):
            with self.subTest(code=code):
                with self.assertRaises(AssuranceError) as caught:
                    receiver.receive_lifecycle(payload)
                self.assertEqual(caught.exception.code, code)

    def test_all_three_profiles_keep_declared_ownership_and_pending_acceptance(self):
        for disposition, initial in (("disposable", "absent"), ("retained", "retained"), ("external", "present")):
            with self.subTest(disposition=disposition):
                subject = profile(disposition, initial)
                result = self.receive(subject)
                self.assertEqual(result["resource"], subject["resource"])
                self.assertEqual(result["requested_profile"], subject["requested_profile"])
                self.assertEqual(result["recorded_operations"], 0)
                self.assertEqual(result["operation_outcomes"], {"requested": 0, "succeeded": 0, "failed": 0, "unresolved": 0})
                self.assertEqual(result["evidence_ceiling"], "declared_lifecycle")
                self.assertEqual(result["configured_execution"], "pending")
                self.assertEqual(result["accountable_acceptance"], "pending")

    def test_ready_requested_create_retains_zero_recorded_operations(self):
        subject = profile()
        subject["readiness"] = {"state": "ready", "observation_ref": "ref:dependency-check"}
        timeline(subject, event(subject, "requested-create", "create", "absent", "absent", "requested"))
        result = self.receive(subject)
        self.assertEqual(result["recorded_operations"], 0)
        self.assertEqual(result["operation_outcomes"]["requested"], 1)
        self.assertEqual(result["readiness"]["state"], "ready")
        self.assertEqual(result["configured_execution"], "pending")

    def test_success_history_is_a_declaration_and_inputs_remain_unchanged(self):
        subject = profile()
        subject["evidence_class"] = "caller_supplied_observation"
        timeline(subject, event(subject, "creation", "create", "absent", "present"),
                 event(subject, "cleanup", "cleanup", "present", "removed"))
        raw = json.dumps(subject, indent=2).encode()
        assessment = receiver.receive_lifecycle(raw)
        result = assessment.to_document()
        self.assertEqual(result["recorded_operations"], 2)
        self.assertEqual(result["operation_outcomes"]["succeeded"], 2)
        self.assertEqual(result["declared_evidence_class"], "caller_supplied_observation")
        self.assertEqual(result["configured_execution"], "pending")
        self.assertEqual(result["accountable_acceptance"], "pending")
        self.assertEqual(result["bindings"]["lifecycle"], digest(raw))
        self.assertEqual(result["bindings"]["canonical_lifecycle"], digest(encoded(subject)))
        result["resource"]["state"] = "unresolved"
        self.assertEqual(assessment.to_document()["resource"]["state"], "removed")
        self.assertEqual(raw, json.dumps(subject, indent=2).encode())
        with self.assertRaises(FrozenInstanceError):
            assessment.canonical_bytes = b"{}"

    def test_receiver_pin_and_schema_bytes_are_independent_of_input(self):
        self.assertEqual(receiver.SOURCE["schema_digest"], "sha256:baf035a23aee30c09f410ec157268a42559a4dde824772ead080ece0f56478ca")
        self.assertIn("@" + receiver.SOURCE["revision"], (ROOT / "requirements-lifecycle.txt").read_text())
        for key, value, code in (("schema_ref", "urn:other-schema", "stale_schema"),
                                 ("schema_version", "9.0.0", "unsupported_version")):
            subject = profile()
            subject[key] = value
            self.rejects(subject, code)
        for key, value in (("revision", "a" * 40), ("source_ref", "ref:caller-selected-source")):
            subject = profile()
            subject["source"][key] = value
            self.rejects(subject, "stale_source")

    def test_wrong_package_or_schema_requires_reviewed_profile(self):
        owner = receiver._owner()
        package = receiver.import_module("lims_eln_contracts")
        with patch.object(receiver.metadata, "version", return_value="0.6.1"):
            self.rejects(profile(), "lifecycle_dependency")
        with patch.object(package, "__version__", "0.6.1"):
            self.rejects(profile(), "lifecycle_dependency")
        with patch.object(owner, "SCHEMA_BYTES", b"{}"):
            self.rejects(profile(), "lifecycle_dependency")
        with patch.object(owner, "CAPABILITY_SCHEMA_BYTES", b"{}"):
            self.rejects(profile(), "lifecycle_dependency")

    def test_installation_provenance_and_import_ownership_match_reviewed_source(self):
        owner = receiver._owner()
        package = receiver.import_module("lims_eln_contracts")
        distribution = receiver.metadata.distribution("lims-eln-program-specification")
        original = json.loads(distribution.read_text("direct_url.json"))
        variants = []
        for key, value in (("commit_id", "a" * 40), ("requested_revision", "develop"), ("vcs", "other")):
            changed = json.loads(json.dumps(original))
            changed["vcs_info"][key] = value
            variants.append(changed)
        variants.extend([dict(original, url="https://github.com/example/other.git"),
                         dict(original, dir_info={"editable": True}), None])
        original_read = distribution.read_text
        for changed in variants:
            with self.subTest(provenance=changed):
                def read(name):
                    return json.dumps(changed) if name == "direct_url.json" else original_read(name)
                with patch.object(receiver.metadata, "distribution", return_value=distribution), patch.object(distribution, "read_text", side_effect=read):
                    self.rejects(profile(), "lifecycle_dependency")
        with patch.object(receiver.metadata, "distribution", return_value=distribution), patch.object(distribution, "read_text", side_effect=lambda name: "" if name == "WHEEL" else original_read(name)):
            self.rejects(profile(), "lifecycle_dependency")
        for module in (package, owner):
            with patch.object(module, "__file__", str(Path(__file__).resolve())):
                self.rejects(profile(), "lifecycle_dependency")

    def test_pythonpath_shadow_package_is_rejected_in_fresh_process(self):
        package = receiver.import_module("lims_eln_contracts")
        with tempfile.TemporaryDirectory() as name:
            shadow = Path(name) / "lims_eln_contracts"
            shutil.copytree(Path(package.__file__).parent, shadow, ignore=shutil.ignore_patterns("__pycache__"))
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/lifecycle_assurance.py"),
                 "--lifecycle", str(ROOT / "examples/database-lifecycle-assurance.json")],
                env={**os.environ, "PYTHONPATH": name}, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("lifecycle_dependency", result.stderr)

    def test_disposable_profile_and_operation_have_owned_authority(self):
        subject = profile()
        subject["resource"]["owner_ref"] = "ref:unrelated-owner"
        self.rejects(subject, "ownership_profile")
        subject = profile()
        operation = event(subject, "creation", "create", "absent", "present")
        operation["authority"]["owner_ref"] = "ref:unrelated-owner"
        self.rejects(timeline(subject, operation), "wrong_owner")

    def test_retained_cleanup_requires_explicit_destructive_decision(self):
        subject = profile("retained", "retained")
        operation = event(subject, "cleanup", "cleanup", "retained", "removed")
        operation["authority"]["basis"] = "invocation_owned"
        self.rejects(timeline(subject, operation), "owner_decision_required")
        operation["authority"]["basis"] = "explicit_owner_decision"
        operation["authority"]["destructive_authorized"] = False
        self.rejects(subject, "destructive_authority_required")
        operation["authority"]["destructive_authorized"] = True
        self.assertEqual(self.receive(subject)["resource"]["state"], "removed")

    def test_external_cleanup_keeps_owner_decision_separate_from_invoker(self):
        subject = profile("external", "present")
        operation = event(subject, "external-cleanup", "cleanup", "present", "removed")
        self.rejects(timeline(subject, operation), "external_cleanup_forbidden")
        operation["authority"]["actor_ref"] = subject["resource"]["owner_ref"]
        result = self.receive(subject)
        self.assertEqual(result["resource"]["state"], "removed")
        self.assertEqual(result["accountable_acceptance"], "pending")

    def test_failed_and_unresolved_cleanup_retain_resource_and_history(self):
        for outcome in ("failed", "unresolved"):
            with self.subTest(outcome=outcome):
                subject = profile()
                timeline(subject, event(subject, "creation", "create", "absent", "present"),
                         event(subject, "cleanup-attempt", "cleanup", "present", "unresolved", outcome))
                result = self.receive(subject)
                self.assertEqual(result["resource"]["state"], "unresolved")
                self.assertEqual(result["unresolved_resource_refs"], ["ref:governance-review-database"])
                self.assertEqual(result["operation_outcomes"][outcome], 1)
                self.assertEqual(result["recorded_operations"], 2)
                subject["unresolved_resource_refs"] = []
                self.rejects(subject, "unresolved_resources")
                timeline(subject, *subject["operations"], event(subject, "cleanup-retry", "cleanup", "unresolved", "removed"))
                result = self.receive(subject)
                self.assertEqual(result["unresolved_resource_refs"], [])
                self.assertEqual(result["operation_outcomes"][outcome], 1)
                self.assertEqual(result["operation_outcomes"]["succeeded"], 2)

    def test_uncertain_creation_needs_new_creation_evidence_before_cleanup(self):
        subject = profile()
        timeline(subject, event(subject, "uncertain-create", "create", "absent", "unresolved", "failed"),
                 event(subject, "unsafe-cleanup", "cleanup", "unresolved", "removed"))
        self.rejects(subject, "unowned_cleanup")

    def test_reconciled_absence_ends_creation_evidence_for_prior_incarnation(self):
        subject = profile()
        history = [event(subject, "first-create", "create", "absent", "present"),
                   event(subject, "uncertain-inspection", "inspect", "present", "unresolved", "unresolved"),
                   event(subject, "absence-check", "inspect", "unresolved", "absent"),
                   event(subject, "next-create", "create", "absent", "unresolved", "failed")]
        timeline(subject, *history, event(subject, "unowned-cleanup", "cleanup", "unresolved", "removed"))
        self.rejects(subject, "unowned_cleanup")
        timeline(subject, *history[:3], event(subject, "new-owned-create", "create", "absent", "present"),
                 event(subject, "new-owned-cleanup", "cleanup", "present", "removed"))
        self.assertEqual(self.receive(subject)["resource"]["state"], "removed")

    def test_removed_incarnation_ends_prior_cleanup_attempt_evidence(self):
        subject = profile()
        timeline(subject, event(subject, "creation", "create", "absent", "present"),
                 event(subject, "cleanup", "cleanup", "present", "removed"),
                 event(subject, "uncertain-inspect", "inspect", "removed", "unresolved", "failed"),
                 event(subject, "claimed-removal", "inspect", "unresolved", "removed"))
        self.rejects(subject, "invalid_transition")

    def test_recreation_after_removal_requires_fresh_owned_creation(self):
        subject = profile()
        history = [event(subject, "first-create", "create", "absent", "present"),
                   event(subject, "first-cleanup", "cleanup", "present", "removed")]
        timeline(subject, *history, event(subject, "second-create", "create", "removed", "present"),
                 event(subject, "second-cleanup", "cleanup", "present", "removed"))
        self.assertEqual(self.receive(subject)["operation_outcomes"]["succeeded"], 4)
        timeline(subject, *history, event(subject, "uncertain-recreation", "create", "removed", "unresolved", "failed"),
                 event(subject, "unowned-next-cleanup", "cleanup", "unresolved", "removed"))
        self.rejects(subject, "unowned_cleanup")

    def test_restore_requires_matching_compatibility_observation(self):
        subject = profile("retained", "retained")
        operation = event(subject, "restore", "restore", "retained", "present")
        self.rejects(timeline(subject, operation), "compatibility_required")
        operation["compatibility"] = {"state": "compatible", "engine_major": 16,
                                      "migration_ref": "ref:reviewed-migration-sequence", "observation_ref": "ref:restore-compatibility"}
        self.rejects(subject, "compatibility_mismatch")
        operation["compatibility"]["engine_major"] = 17
        self.assertEqual(self.receive(subject)["operation_outcomes"]["succeeded"], 1)

    def capability(self, subject):
        capability = json.loads((ROOT / "examples/assurance-capability.json").read_bytes())
        capability["runtime"].update(state_adapter="postgresql", state_lifetime="database")
        capability["shared_contracts"]["version_compatible"] = False
        payload = encoded(capability)
        subject["composition"] = {"state": "observed", "capability_ref": "ref:reviewed-composition", "capability_digest": digest(payload)}
        return capability, payload

    def test_capability_v1_composition_keeps_readiness_and_acceptance_separate(self):
        subject = profile("retained", "present")
        _, payload = self.capability(subject)
        result = self.receive(subject, payload)
        self.assertEqual(result["composition"]["state"], "observed")
        self.assertEqual(result["bindings"]["capability"], digest(payload))
        self.assertEqual(result["readiness"]["state"], "not_observed")
        self.assertEqual(result["configured_execution"], "pending")

    def test_composition_requires_exact_bytes_and_database_lifetime(self):
        subject = profile("external", "present")
        capability, payload = self.capability(subject)
        self.rejects(subject, "composition_unresolved")
        self.rejects(subject, "composition_digest", payload + b"\n")
        capability["runtime"].update(state_adapter="process_local", state_lifetime="process")
        payload = encoded(capability)
        subject["composition"]["capability_digest"] = digest(payload)
        self.rejects(subject, "composition_mismatch", payload)
        self.rejects(profile(), "composition_mismatch", payload)

    def test_cli_returns_normalized_claims_and_value_free_errors(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "profile.json"
            path.write_bytes(encoded(profile()))
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(receiver.main(["--lifecycle", str(path)]), 0)
            self.assertEqual(json.loads(output.getvalue())["evidence_ceiling"], "declared_lifecycle")
            self.assertEqual(errors.getvalue(), "")
            path.write_bytes(b'{"private-input-sentinel":true,"private-input-sentinel":false}')
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(receiver.main(["--lifecycle", str(path)]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("json_duplicate_key", errors.getvalue())
            self.assertNotIn("private-input-sentinel", errors.getvalue())
            path.write_bytes(b" " * (receiver.MAX_BYTES + 1))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(receiver.main(["--lifecycle", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
