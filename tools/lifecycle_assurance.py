#!/usr/bin/env python3
"""Receive a declared lifecycle through Program's pinned semantic owner."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module, metadata
import json
from pathlib import Path
import sys

from assurance_companion import AssuranceError, digest, encoded, read_regular

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / "contract-resources/database-lifecycle-source.json").read_bytes())
MAX_BYTES = 131072


@dataclass(frozen=True, slots=True)
class LifecycleAssessment:
    """An immutable normalized return; callers own every exported document."""

    canonical_bytes: bytes

    def to_document(self) -> dict:
        return json.loads(self.canonical_bytes)


def _owner():
    try:
        owner = import_module("lims_eln_contracts.database_lifecycle")
        package = import_module("lims_eln_contracts")
        distribution = metadata.distribution("lims-eln-program-specification")
        version = metadata.version("lims-eln-program-specification")
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as error:
        if isinstance(error, ModuleNotFoundError) and error.name not in {
            "lims_eln_contracts", "lims_eln_contracts.database_lifecycle"
        }:
            raise
        raise AssuranceError("lifecycle_dependency", "Install the exact requirements-lifecycle.txt profile in its own environment.") from None
    try:
        provenance = json.loads(distribution.read_text("direct_url.json") or "null")
        wheel = distribution.read_text("WHEEL") or ""
        expected_url = "https://github.com/" + SOURCE["repository"] + ".git"
        expected_vcs = {"vcs": "git", "requested_revision": SOURCE["revision"], "commit_id": SOURCE["revision"]}
        installed_files = {str(path) for path in distribution.files or ()}
        paths_owned = all(
            relative in installed_files
            and Path(module.__file__).resolve(strict=True) == Path(distribution.locate_file(relative)).resolve(strict=True)
            for module, relative in (
                (package, "lims_eln_contracts/__init__.py"),
                (owner, "lims_eln_contracts/database_lifecycle.py"),
            )
        )
        provenance_matches = (
            type(provenance) is dict
            and provenance.get("url") == expected_url
            and provenance.get("vcs_info") == expected_vcs
            and "dir_info" not in provenance
            and "archive_info" not in provenance
            and wheel.startswith("Wheel-Version: 1.")
            and paths_owned
        )
    except (OSError, ValueError, TypeError, AttributeError):
        provenance_matches = False
    if not provenance_matches:
        raise AssuranceError("lifecycle_dependency", "Install the exact Git revision as a wheel and use its owned package paths.")
    if (version != SOURCE["package_version"]
            or package.__version__ != SOURCE["package_version"]
            or owner.SCHEMA_ID != SOURCE["schema_id"]
            or digest(owner.SCHEMA_BYTES) != SOURCE["schema_digest"]
            or digest(owner.CAPABILITY_SCHEMA_BYTES) != SOURCE["capability_schema_digest"]):
        raise AssuranceError("lifecycle_dependency", "Restore the reviewed Program package and schema coordinate.")
    return owner


def receive_lifecycle(payload: bytes, *, capability_payload: bytes | None = None) -> LifecycleAssessment:
    """Admit source semantics, then map declarations to bounded assurance claims.

    Governance retains O(B + E) memory and traversal for bounded bytes B and
    events E. Canonical encoding also sorts the bounded object key sets. Program
    owns semantic admission; this receiver performs zero database operations.
    """
    owner = _owner()
    expected = owner.LifecycleSource(SOURCE["source_ref"], SOURCE["revision"], SOURCE["schema_digest"])
    try:
        admitted = owner.admit_lifecycle_profile(payload, expected_source=expected, capability_payload=capability_payload)
    except owner.LifecycleAdmissionError as error:
        raise AssuranceError(error.code, "Retain the input and reconcile its lifecycle with the Program guide before receiving it again.") from None
    profile = json.loads(admitted.canonical_bytes)
    outcomes = {name: 0 for name in ("requested", "succeeded", "failed", "unresolved")}
    for event in profile["operations"]:
        outcomes[event["outcome"]] += 1
    result = {
        "assessment_type": "database_lifecycle_assurance",
        "source": dict(SOURCE),
        "bindings": {
            "lifecycle": digest(payload),
            "canonical_lifecycle": digest(admitted.canonical_bytes),
            "capability": None if capability_payload is None else digest(capability_payload),
        },
        "profile_ref": profile["profile_ref"],
        "declared_evidence_class": profile["evidence_class"],
        "invocation": profile["invocation"],
        "requested_profile": profile["requested_profile"],
        "resource": profile["resource"],
        "composition": profile["composition"],
        "readiness": profile["readiness"],
        "operation_outcomes": outcomes,
        "recorded_operations": admitted.executed_operations,
        "unresolved_resource_refs": list(admitted.unresolved_resource_refs),
        "evidence_ceiling": "declared_lifecycle",
        "configured_execution": "pending",
        "accountable_acceptance": "pending",
    }
    return LifecycleAssessment(encoded(result))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycle", type=Path, required=True)
    parser.add_argument("--capability", type=Path)
    args = parser.parse_args(argv)
    try:
        result = receive_lifecycle(
            read_regular(args.lifecycle, max_bytes=MAX_BYTES),
            capability_payload=None if args.capability is None else read_regular(args.capability, max_bytes=MAX_BYTES),
        )
        print(result.canonical_bytes.decode("utf-8"))
    except AssuranceError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
