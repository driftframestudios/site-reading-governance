#!/usr/bin/env python3
"""Receive bounded evidence and carry scoped review through immutable successors."""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Mapping, Protocol

from validate_governance import SchemaValidator, load_json_bytes

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/administrative-assurance.schema.json"
CAPABILITY_SCHEMA = ROOT / "contract-resources/workbench-capabilities.v1.schema.json"
MAX_BYTES = 4 * 1024 * 1024
ROLES = frozenset(("pack", "study", "report", "capability"))
STUDY_ROLES = frozenset(("pack", "study", "report"))
STUDY_BINDINGS = frozenset(("pack", "study", "report", "source", "oracle", "specification", "execution", "catalog", "policy", "scoring", "intended_use"))
DEPENDENCIES = {
    "harness_behavior": STUDY_BINDINGS,
    "output_comparison": STUDY_BINDINGS,
    "population_effect": STUDY_BINDINGS,
    "capability_composition": frozenset(("capability", "intended_use")),
    "configured_execution": frozenset(("capability", "intended_use")),
}
BINDINGS = STUDY_BINDINGS | {"capability"}


class AssuranceError(ValueError):
    """Expose a stable code and an owned recovery route, keeping payloads local."""

    def __init__(self, code: str, recovery: str):
        self.code = code
        self.recovery = recovery
        super().__init__(f"{code}: {recovery}")


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_unicode(value: object) -> None:
    """Require UTF-8 scalar text in JSON keys and values, preserving exact text."""
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_unicode(key)
            _validate_unicode(item)
    elif isinstance(value, list):
        for item in value:
            _validate_unicode(item)


def document(payload: bytes, label: str) -> dict:
    if type(payload) is not bytes or len(payload) > MAX_BYTES:
        raise AssuranceError("input_size", f"Supply bounded UTF-8 JSON for {label}.")
    try:
        value = load_json_bytes(payload)
        _validate_unicode(value)
    except (ValueError, UnicodeError, RecursionError):
        raise AssuranceError("input_json", f"Supply strict, finite JSON with UTF-8 scalar text for {label}.") from None
    if type(value) is not dict:
        raise AssuranceError("input_object", f"Supply one object for {label}.")
    return value


def validate_record(record: dict) -> None:
    """Check the closed schema and the profile's cross-field invariants."""
    try:
        _validate_unicode(record)
        findings = SchemaValidator(SCHEMA).validate(record)
    except (ValueError, KeyError, RecursionError):
        raise AssuranceError("record_shape", "Use the declared assurance profile and its bounded fields.") from None
    if findings:
        raise AssuranceError("record_shape", "Use the declared assurance profile and its bounded fields.")
    roles = [item["role"] for item in record["artifacts"]]
    identifiers = [item["artifact_id"] for item in record["artifacts"]]
    claim_ids = [item["claim_id"] for item in record["claims"]]
    if len(set(roles)) != len(roles) or len(set(identifiers)) != len(identifiers) or len(set(claim_ids)) != len(claim_ids):
        raise AssuranceError("duplicate_reference", "Give each artifact role, artifact ID, and claim ID one owner.")
    for claim in record["claims"]:
        if set(claim["depends_on"]) != DEPENDENCIES[claim["claim_type"]]:
            raise AssuranceError("claim_dependencies", "Retain the profile's complete dependency set for each claim type.")
    if record["record_kind"] == "request":
        if any(c["review_state"] != "pending" or c["evidence_ceiling"] != "pending" for c in record["claims"]):
            raise AssuranceError("request_review", "Begin a receiving request with pending review and evidence standing.")
        return
    assessment = record["assessment"]
    counts = assessment["population"]
    if counts is not None:
        partition = sum(counts[key] for key in ("completed", "pending", "abstained", "failed", "cancelled", "excluded"))
        if counts["planned"] < 2 or partition != counts["planned"] or not 0 <= counts["scored"] <= counts["completed"] <= counts["attempted"] <= counts["planned"] or counts["usable"] > counts["completed"]:
            raise AssuranceError("population_partition", "Reconcile the populations through the Program interpretation owner.")
    elif set(roles) != {"capability"}:
        raise AssuranceError("population_required", "Receive the complete study population from its owner.")
    for claim in record["claims"]:
        if claim["claim_type"] in {"configured_execution", "population_effect"} and claim["review_state"] != "held":
            raise AssuranceError("claim_ceiling", "Receive configured or population-use evidence through its separate review route.")
        if claim["evidence_ceiling"] not in {"pending", "composition_only", assessment["evidence_class"]}:
            raise AssuranceError("claim_ceiling", "Retain the received evidence class through review.")


    _validate_assessment(record)


def _claim_supported(kind: str, roles: set[str], population: Mapping[str, int] | None) -> bool:
    """Choose a review entry from supplied roles and observed work, in O(1)."""
    if kind == "capability_composition":
        return "capability" in roles
    if not STUDY_ROLES.issubset(roles) or population is None:
        return False
    if kind == "harness_behavior":
        return population["attempted"] > 0
    if kind == "output_comparison":
        return all(population[key] > 0 for key in ("completed", "usable", "scored"))
    return False


def _validate_assessment(record: dict) -> None:
    """Reconcile admitted metadata in O(artifacts + claims); source owners admit bytes."""
    roles = {artifact["role"] for artifact in record["artifacts"]}
    study_roles = roles & STUDY_ROLES
    if study_roles and study_roles != STUDY_ROLES:
        raise AssuranceError("study_membership", "Receive the pack, study, and report together.")
    assessment = record["assessment"]
    bindings = assessment["bindings"]
    expected_bindings = roles | {"intended_use"}
    if study_roles:
        expected_bindings |= STUDY_BINDINGS
    if set(bindings) != expected_bindings:
        raise AssuranceError("assessment_bindings", "Re-admit the supplied artifacts to restore their complete binding set.")
    if bindings["intended_use"] != digest(record["intended_use"].encode("utf-8")):
        raise AssuranceError("assessment_binding", "Re-admit the artifacts for the current intended use.")
    for artifact in record["artifacts"]:
        if bindings[artifact["role"]] != artifact["digest"]:
            raise AssuranceError("assessment_binding", "Re-admit the changed artifact before reviewing its claims.")
    population = assessment["population"]
    if study_roles:
        if population is None:
            raise AssuranceError("population_required", "Receive the study's complete population accounting.")
        if assessment["evidence_class"] not in {"fixture_demonstration", "caller_supplied_synthetic"}:
            raise AssuranceError("assessment_evidence", "Retain the study owner's declared evidence class.")
        disagreements = assessment["scientific_disagreements"]
        if disagreements is None or disagreements > population["scored"]:
            raise AssuranceError("assessment_evidence", "Bind scientific disagreements to the scored population.")
    elif (population is not None or assessment["represented_dimensions"]
          or assessment["scientific_disagreements"] is not None
          or assessment["evidence_class"] != "composition_only"):
        raise AssuranceError("assessment_evidence", "Keep capability composition distinct from study observations.")
    for claim in record["claims"]:
        ceiling = ("composition_only" if claim["claim_type"] == "capability_composition"
                   else assessment["evidence_class"])
        if claim["review_state"] in {"review_ready", "reviewed"}:
            if not _claim_supported(claim["claim_type"], roles, population):
                raise AssuranceError("claim_support", "Receive the artifacts and observations required by this claim before review.")
            if claim["evidence_ceiling"] != ceiling:
                raise AssuranceError("claim_ceiling", "Retain the evidence class established by the claim's source.")
        elif claim["evidence_ceiling"] not in {"pending", ceiling}:
            raise AssuranceError("claim_ceiling", "Retain the prior source's ceiling while the claim is held.")
        change = record["change"]
        if (change and set(change["bindings"]) & set(claim["depends_on"])
                and claim["review_state"] != "held"):
            raise AssuranceError("claim_invalidation", "Re-admit affected evidence before creating a fresh review entry.")


@dataclass(frozen=True)
class StudyAssessment:
    bindings: Mapping[str, str]
    population: Mapping[str, int]
    represented_dimensions: tuple[str, ...]
    evidence_class: str
    scientific_disagreements: int


class StudyReceiver(Protocol):
    def __call__(self, artifacts: Mapping[str, bytes]) -> StudyAssessment: ...


def receive(request_bytes: bytes, artifacts: Mapping[str, bytes], *, study_receiver: StudyReceiver | None = None) -> dict:
    """Own one JSON snapshot; resolve only caller-supplied, digest-bound artifacts.

    Governance work is O(B + A + C) time and O(B + A + C) space for bounded
    input bytes B, artifacts A, and claims C. Upstream scoring retains its
    separately owned cost. Schema preparation occurs once per validation call.
    """
    result = document(request_bytes, "request")
    validate_record(result)
    if result["record_kind"] != "request":
        raise AssuranceError("request_kind", "Receive a request; preserve earlier companion records as evidence.")
    expected = {item["role"]: item for item in result["artifacts"]}
    if set(artifacts) != set(expected):
        raise AssuranceError("artifact_membership", "Supply exactly the artifact roles declared by the request.")
    study_roles = set(expected) & STUDY_ROLES
    if study_roles and study_roles != STUDY_ROLES:
        raise AssuranceError("study_membership", "Receive pack, study, and report together.")
    decoded = {}
    for role, reference in expected.items():
        payload = artifacts[role]
        decoded[role] = document(payload, role)
        if digest(payload) != reference["digest"]:
            raise AssuranceError("artifact_digest", f"Reconcile the {role} bytes with their accepted reference.")
        schema_id = decoded[role].get("contract_id") if role == "capability" else decoded[role].get("$schema")
        if schema_id != reference["schema_id"]:
            raise AssuranceError("artifact_schema", f"Receive the declared {role} schema identity.")
    bindings = {role: ref["digest"] for role, ref in expected.items()}
    bindings["intended_use"] = digest(result["intended_use"].encode("utf-8"))
    assessment = {"evidence_class": "composition_only", "bindings": bindings, "population": None, "represented_dimensions": [], "scientific_disagreements": None, "configured_execution": "pending", "remote_authority": "pending"}
    if "capability" in expected:
        if SchemaValidator(CAPABILITY_SCHEMA).validate(decoded["capability"]):
            raise AssuranceError("capability_contract", "Receive the Program-owned capability contract.")
    if study_roles:
        if study_receiver is None:
            from assurance_upstream import receive_study
            study_receiver = receive_study
        observed = study_receiver({role: artifacts[role] for role in STUDY_ROLES})
        bindings.update(observed.bindings)
        assessment.update(evidence_class=observed.evidence_class, population=dict(observed.population), represented_dimensions=list(observed.represented_dimensions), scientific_disagreements=observed.scientific_disagreements)
    result["record_kind"] = "companion"
    result["assessment"] = assessment
    for claim in result["claims"]:
        kind = claim["claim_type"]
        supported = _claim_supported(claim["claim_type"], set(expected), assessment["population"])
        claim["review_state"] = "review_ready" if supported else "held"
        claim["evidence_ceiling"] = "composition_only" if kind == "capability_composition" and supported else assessment["evidence_class"] if supported else "pending"
        claim["review_note"] = "A named reviewer can assess this statement within its recorded evidence class." if supported else "Receive evidence for this claim's population, environment, and authority before scoped review."
    validate_record(result)
    return result


def _successor(record: dict, successor_id: str, reason: str) -> dict:
    validate_record(record)
    if (record["record_kind"] != "companion"
            or successor_id in (record["companion_id"], record["supersedes"])
            or not reason.strip()):
        raise AssuranceError("successor_identity", "Choose a fresh companion identity beyond the current record and its named predecessor, with a decision-changing reason.")
    result = copy.deepcopy(record)
    result["companion_id"] = successor_id
    result["supersedes"] = record["companion_id"]
    result["prior_digest"] = digest(encoded(record))
    return result


def record_review(record: dict, *, claim_id: str, successor_id: str, note: str) -> dict:
    """Record a caller's scoped review while retaining the evidence ceiling."""
    result = _successor(record, successor_id, note)
    selected = [c for c in result["claims"] if c["claim_id"] == claim_id]
    if len(selected) != 1 or selected[0]["review_state"] != "review_ready":
        raise AssuranceError("review_entry", "Select one review-ready claim; receive changed evidence through a fresh request.")
    selected[0].update(review_state="reviewed", review_note=note)
    validate_record(result)
    return result


def invalidate(record: dict, *, changed_bindings: frozenset[str], successor_id: str, reason: str) -> dict:
    """Hold affected claims in a successor while preserving the prior account."""
    if not changed_bindings or not changed_bindings <= BINDINGS:
        raise AssuranceError("change_binding", "Name the profile bindings changed by this event.")
    result = _successor(record, successor_id, reason)
    for claim in result["claims"]:
        if changed_bindings.intersection(claim["depends_on"]):
            claim.update(review_state="held", review_note=reason)
    result["change"] = {"bindings": sorted(changed_bindings), "reason": reason}
    validate_record(result)
    return result


def render_markdown(record: dict) -> str:
    """Render literal-safe review text; source records retain detailed lineage."""
    validate_record(record)
    text = json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)
    longest = max((len(part) for part in __import__("re").findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return "# Administrative assurance companion\n\nReview the statement, evidence class, authority, and successor route together.\n\n" + fence + "json\n" + text + "\n" + fence + "\n"


def read_regular(path: Path) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise AssuranceError("input_file", "Select an owned regular JSON file.")
            payload = stream.read(MAX_BYTES + 1)
    except OSError:
        raise AssuranceError("input_file", "Select an accessible owned regular JSON file.") from None
    if len(payload) > MAX_BYTES:
        raise AssuranceError("input_size", "Supply a JSON artifact within the profile byte budget.")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--artifact", action="append", default=[], metavar="ROLE=PATH")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args(argv)
    try:
        paths = {}
        for item in args.artifact:
            role, separator, path = item.partition("=")
            if not separator or role not in ROLES or role in paths:
                raise AssuranceError("artifact_argument", "Supply each declared ROLE=PATH once.")
            paths[role] = Path(path)
        result = receive(read_regular(args.request), {role: read_regular(path) for role, path in paths.items()})
        print(render_markdown(result) if args.markdown else encoded(result).decode("utf-8"))
        return 0
    except AssuranceError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
