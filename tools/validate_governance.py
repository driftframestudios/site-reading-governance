#!/usr/bin/env python3
"""Validate governance schemas, examples, references, and semantic invariants."""

from __future__ import annotations

import argparse
import datetime as dt
from hashlib import sha256
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urldefrag, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXAMPLE_DIR = ROOT / "examples"
RULESET_DIR = ROOT / "rulesets"
WORKFLOW_DIR = ROOT / ".github" / "workflows"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_RELEASE = "2.0.1"
SCHEMA_ID_PREFIX = "https://schemas.driftframe.org/site-reading-governance/v2.0/"
SCHEMA_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*\.schema\.json$")
DOCUMENT_PATH_PATTERN = re.compile(
    r"^(?:[A-Za-z0-9][A-Za-z0-9._-]*/)*"
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.json$"
)
RFC3339_DATE_TIME = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:(?:[0-5][0-9]|60)"
    r"(?:\.[0-9]+)?"
    r"(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$"
)
RELEASE_TAG_INCLUDES = {
    "refs/tags/v*",
    "refs/tags/spec-v*",
    "refs/tags/candidate-v*",
    "refs/tags/governance-v*",
    "refs/tags/comparison-v*",
    "refs/tags/forecast-*",
}
SUBSTANTIVE_SIMULATED_RECEIPT_FAMILIES = {
    "configured_vendor_environments",
    "representative_migration_restore_rehearsals",
    "production_security_observability",
    "accountable_scientific_quality_regulatory_acceptance",
}
ROOT_ORIENTATION_SCHEMAS = {
    "machine-node.json": "machine-node.schema.json",
    "first-receipt.json": "first-receipt.schema.json",
    "coordination-horizon.json": "coordination-horizon.schema.json",
    "promotion-receipt.json": "promotion-receipt.schema.json",
}
ROOT_ORIENTATION_CONTRACTS = {
    "CONTRACT-SELECTED-FUTURE-CLOSURE-002": "2.0.0",
    "CONTRACT-AUTOMATION-BRANCH-POLICY-001": "1.0.0",
}
ROOT_ORIENTATION_CONTRACT_FILES = {
    "CONTRACT-SELECTED-FUTURE-CLOSURE-002": (
        SCHEMA_DIR / "simulated-receipt-closure.schema.json"
    ),
    "CONTRACT-AUTOMATION-BRANCH-POLICY-001": ROOT / "tools" / "check_branch_flow.py",
}
ROOT_ORIENTATION_CAMPAIGNS = {
    "LIMS-ELN-OPEN-RECEIPTS",
    "COMPARATIVE-LITERACY-COLLABORATION",
    "SITE-READING-SYSTEM",
}
ZERO_COMMIT = "0" * 40
ZERO_DIGEST = "sha256:" + ("0" * 64)
EFFECT_CLASS_RANK = {
    "read": 0,
    "narrow_write": 1,
    "broad_write": 2,
    "irreversible_effect": 3,
}
LEGACY_COORDINATOR = re.compile(
    r"\bnow\s*/\s*next\s*/\s*later\s+coordinator\b",
    re.IGNORECASE,
)
SUPPORTED_SCHEMA_KEYWORDS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "description",
    "else",
    "enum",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "if",
    "items",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "then",
    "title",
    "type",
    "uniqueItems",
}
SCHEMA_MAP_KEYWORDS = {"$defs", "properties"}
SCHEMA_ARRAY_KEYWORDS = {"allOf", "anyOf", "oneOf"}
SCHEMA_VALUE_KEYWORDS = {"additionalProperties", "else", "if", "items", "then"}


@dataclass(frozen=True)
class Finding:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class DuplicateKeyError(ValueError):
    """Signal duplicate JSON keys with the key name preserved."""


class NonFiniteNumberError(ValueError):
    """Signal a numeric token outside the JSON number grammar."""


class ReferenceResolutionError(ValueError):
    """Signal a schema reference outside its bounded schema directory."""


class ContractInputError(ValueError):
    """Signal a reusable-workflow input outside the bounded path grammar."""


def _object_with_unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_non_finite(token: str) -> None:
    raise NonFiniteNumberError(f"non-finite numeric token {token!r} is outside JSON")


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise NonFiniteNumberError(
            f"numeric token {token!r} exceeds the finite JSON domain"
        )
    return value


def load_json(path: Path) -> Any:
    """Load strict UTF-8 JSON and preserve a precise source-path failure."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            object_pairs_hook=_object_with_unique_keys,
            parse_constant=_reject_non_finite,
            parse_float=_parse_finite_float,
        )


class SchemaValidator:
    """Evaluate the JSON Schema subset used by this governance package."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path.resolve()
        self.reference_root = self.schema_path.parent
        self.document_cache: dict[Path, Any] = {}

    def validate(self, instance: Any) -> list[Finding]:
        schema = self._load_schema(self.schema_path)
        return self._evaluate(instance, schema, "$", self.schema_path)

    def _load_schema(self, path: Path) -> Any:
        resolved = path.resolve()
        if resolved not in self.document_cache:
            self.document_cache[resolved] = load_json(resolved)
        return self.document_cache[resolved]

    def _resolve_reference(self, reference: str, base_path: Path) -> tuple[Any, Path]:
        location, fragment = urldefrag(reference)
        parsed = urlsplit(location)
        relative = Path(location)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.query
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise ReferenceResolutionError(
                f"schema reference {reference!r} leaves the bounded schema directory"
            )
        target_path = (base_path.parent / relative).resolve() if location else base_path
        try:
            target_path.relative_to(self.reference_root)
        except ValueError as exc:
            raise ReferenceResolutionError(
                f"schema reference {reference!r} leaves the bounded schema directory"
            ) from exc
        target = self._load_schema(target_path)
        if fragment:
            for token in fragment.lstrip("/").split("/"):
                decoded = token.replace("~1", "/").replace("~0", "~")
                target = target[decoded]
        return target, target_path

    def _evaluate(
        self,
        instance: Any,
        schema: Any,
        path: str,
        base_path: Path,
    ) -> list[Finding]:
        if isinstance(schema, bool):
            return [] if schema else [Finding(path, "boolean schema rejects this value")]

        findings: list[Finding] = []

        if "$ref" in schema:
            target, target_path = self._resolve_reference(schema["$ref"], base_path)
            findings.extend(self._evaluate(instance, target, path, target_path))
            sibling_schema = {key: value for key, value in schema.items() if key != "$ref"}
            if sibling_schema:
                findings.extend(self._evaluate(instance, sibling_schema, path, base_path))
            return findings

        for item in schema.get("allOf", []):
            findings.extend(self._evaluate(instance, item, path, base_path))

        if "anyOf" in schema:
            candidates = [
                self._evaluate(instance, item, path, base_path)
                for item in schema["anyOf"]
            ]
            if all(candidate for candidate in candidates):
                findings.append(Finding(path, "value satisfies zero anyOf branches"))

        if "oneOf" in schema:
            matches = sum(
                1
                for item in schema["oneOf"]
                if not self._evaluate(instance, item, path, base_path)
            )
            if matches != 1:
                findings.append(
                    Finding(path, f"value satisfies {matches} oneOf branches; expected one")
                )

        condition = schema.get("if")
        if condition is not None:
            condition_matches = not self._evaluate(instance, condition, path, base_path)
            branch = schema.get("then") if condition_matches else schema.get("else")
            if branch is not None:
                findings.extend(self._evaluate(instance, branch, path, base_path))

        if "const" in schema and instance != schema["const"]:
            findings.append(Finding(path, f"value must equal {schema['const']!r}"))

        if "enum" in schema and instance not in schema["enum"]:
            findings.append(Finding(path, f"value {instance!r} is outside the enum"))

        expected_type = schema.get("type")
        if expected_type and not self._matches_type(instance, expected_type):
            findings.append(Finding(path, f"value must have type {expected_type}"))
            return findings

        if isinstance(instance, dict):
            findings.extend(self._evaluate_object(instance, schema, path, base_path))
        elif isinstance(instance, list):
            findings.extend(self._evaluate_array(instance, schema, path, base_path))
        elif isinstance(instance, str):
            findings.extend(self._evaluate_string(instance, schema, path))
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            findings.extend(self._evaluate_number(instance, schema, path))

        return findings

    @staticmethod
    def _matches_type(instance: Any, expected: str | list[str]) -> bool:
        if isinstance(expected, list):
            return any(SchemaValidator._matches_type(instance, item) for item in expected)
        checks = {
            "object": lambda value: isinstance(value, dict),
            "array": lambda value: isinstance(value, list),
            "string": lambda value: isinstance(value, str),
            "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
            "number": lambda value: isinstance(value, (int, float))
            and not isinstance(value, bool),
            "boolean": lambda value: isinstance(value, bool),
            "null": lambda value: value is None,
        }
        return checks[expected](instance)

    def _evaluate_object(
        self,
        instance: dict[str, Any],
        schema: dict[str, Any],
        path: str,
        base_path: Path,
    ) -> list[Finding]:
        findings: list[Finding] = []
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                findings.append(Finding(path, f"required property {key!r} is absent"))

        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                findings.extend(
                    self._evaluate(value, properties[key], child_path, base_path)
                )
            elif schema.get("additionalProperties") is False:
                findings.append(Finding(child_path, "property is outside the contract"))
            elif isinstance(schema.get("additionalProperties"), dict):
                findings.extend(
                    self._evaluate(
                        value,
                        schema["additionalProperties"],
                        child_path,
                        base_path,
                    )
                )
        return findings

    def _evaluate_array(
        self,
        instance: list[Any],
        schema: dict[str, Any],
        path: str,
        base_path: Path,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if len(instance) < schema.get("minItems", 0):
            findings.append(Finding(path, "array is shorter than minItems"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            findings.append(Finding(path, "array is longer than maxItems"))
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in instance]
            if len(serialized) != len(set(serialized)):
                findings.append(Finding(path, "array values must be unique"))
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                findings.extend(
                    self._evaluate(value, item_schema, f"{path}[{index}]", base_path)
                )
        return findings

    @staticmethod
    def _evaluate_string(
        instance: str,
        schema: dict[str, Any],
        path: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if len(instance) < schema.get("minLength", 0):
            findings.append(Finding(path, "string is shorter than minLength"))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            findings.append(Finding(path, "string is longer than maxLength"))
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            findings.append(Finding(path, "string does not match the required pattern"))
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(instance)
            except ValueError:
                findings.append(Finding(path, "string must be an ISO 8601 date"))
        if schema.get("format") == "date-time":
            match = RFC3339_DATE_TIME.fullmatch(instance)
            if match is None:
                findings.append(
                    Finding(path, "string must be an RFC 3339 date-time with timezone")
                )
            else:
                try:
                    dt.date.fromisoformat(match.group("date"))
                except ValueError:
                    findings.append(
                        Finding(path, "string must carry a valid RFC 3339 calendar date")
                    )
        return findings

    @staticmethod
    def _evaluate_number(
        instance: int | float,
        schema: dict[str, Any],
        path: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if isinstance(instance, float) and not math.isfinite(instance):
            return [Finding(path, "number must be finite")]
        if "minimum" in schema and instance < schema["minimum"]:
            findings.append(Finding(path, "number is below minimum"))
        if "maximum" in schema and instance > schema["maximum"]:
            findings.append(Finding(path, "number is above maximum"))
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            findings.append(Finding(path, "number must exceed exclusiveMinimum"))
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            findings.append(Finding(path, "number must be below exclusiveMaximum"))
        return findings


def validate_schema_catalog() -> list[Finding]:
    """Check schema identity, draft, references, and root naming."""
    findings: list[Finding] = []
    ids: set[str] = set()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            schema = load_json(path)
        except (
            OSError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ) as exc:
            findings.append(Finding(str(path.relative_to(ROOT)), str(exc)))
            continue
        relative = str(path.relative_to(ROOT))
        if schema.get("$schema") != DRAFT:
            findings.append(Finding(relative, "schema must declare JSON Schema 2020-12"))
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id.startswith("https://"):
            findings.append(Finding(relative, "schema must carry a stable HTTPS $id"))
        elif not schema_id.startswith(SCHEMA_ID_PREFIX):
            findings.append(
                Finding(
                    relative,
                    f"schema $id must use the {SCHEMA_RELEASE} release coordinate",
                )
            )
        elif schema_id in ids:
            findings.append(Finding(relative, f"schema $id {schema_id!r} is duplicated"))
        else:
            ids.add(schema_id)
        if path.name != "common.schema.json" and schema.get("type") != "object":
            findings.append(Finding(relative, "governance record root must be an object"))
        findings.extend(_validate_schema_keywords(schema, relative))
        findings.extend(_walk_references(schema, path, relative))
    return findings


def _validate_schema_keywords(
    schema: Any,
    location: str,
) -> list[Finding]:
    """Reject schema vocabulary that the dependency-free evaluator cannot enforce."""
    if isinstance(schema, bool):
        return []
    if not isinstance(schema, dict):
        return [Finding(location, "schema position must contain an object or boolean")]

    findings: list[Finding] = []
    unsupported = set(schema) - SUPPORTED_SCHEMA_KEYWORDS
    for keyword in sorted(unsupported):
        findings.append(
            Finding(
                location,
                f"schema keyword {keyword!r} is outside the supported evaluator vocabulary",
            )
        )
    for keyword in SCHEMA_MAP_KEYWORDS:
        value = schema.get(keyword, {})
        if isinstance(value, dict):
            for name, child in value.items():
                findings.extend(
                    _validate_schema_keywords(child, f"{location}/{keyword}/{name}")
                )
    for keyword in SCHEMA_ARRAY_KEYWORDS:
        value = schema.get(keyword, [])
        if isinstance(value, list):
            for index, child in enumerate(value):
                findings.extend(
                    _validate_schema_keywords(child, f"{location}/{keyword}/{index}")
                )
    for keyword in SCHEMA_VALUE_KEYWORDS:
        value = schema.get(keyword)
        if isinstance(value, (dict, bool)):
            findings.extend(
                _validate_schema_keywords(value, f"{location}/{keyword}")
            )
    return findings


def _walk_references(value: Any, base_path: Path, location: str) -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str):
            try:
                SchemaValidator(base_path)._resolve_reference(reference, base_path)
            except (
                OSError,
                KeyError,
                json.JSONDecodeError,
                DuplicateKeyError,
                NonFiniteNumberError,
                ReferenceResolutionError,
            ) as exc:
                findings.append(Finding(location, f"reference {reference!r} fails: {exc}"))
        for key, child in value.items():
            findings.extend(_walk_references(child, base_path, f"{location}/{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_walk_references(child, base_path, f"{location}/{index}"))
    return findings


def validate_examples() -> list[Finding]:
    """Validate every mapped example and the cross-record semantic invariants."""
    findings: list[Finding] = []
    mapping = load_json(EXAMPLE_DIR / "example-map.json")["schema_map"]
    expected_schemas = {
        path.name for path in SCHEMA_DIR.glob("*.schema.json")
        if path.name != "common.schema.json"
    }
    mapped_schemas = set(mapping.values())
    if expected_schemas != mapped_schemas:
        findings.append(
            Finding(
                "examples/example-map.json",
                f"schema coverage differs: expected {sorted(expected_schemas)}, "
                f"mapped {sorted(mapped_schemas)}",
            )
        )

    records: dict[str, Any] = {}
    for example_name, schema_name in mapping.items():
        example_path = EXAMPLE_DIR / example_name
        schema_path = SCHEMA_DIR / schema_name
        try:
            record = load_json(example_path)
            records[example_name] = record
            metadata = record.get("metadata", {})
            if metadata.get("schema_version") != SCHEMA_RELEASE:
                findings.append(
                    Finding(
                        f"examples/{example_name}.metadata.schema_version",
                        f"governance schema version must equal {SCHEMA_RELEASE}",
                    )
                )
            for finding in SchemaValidator(schema_path).validate(record):
                findings.append(
                    Finding(f"examples/{example_name}{finding.path[1:]}", finding.message)
                )
        except (
            OSError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ) as exc:
            findings.append(Finding(f"examples/{example_name}", str(exc)))

    constellation = records.get("constellation.json", {})
    roles = [item["role"] for item in constellation.get("repositories", [])]
    if len(roles) != len(set(roles)):
        findings.append(Finding("examples/constellation.json", "repository roles must be unique"))

    comparison = records.get("comparison.json", {})
    results = comparison.get("results", [])
    summary = comparison.get("summary", {})
    if summary.get("total") != len(results):
        findings.append(
            Finding("examples/comparison.json", "summary total must equal result count")
        )
    pending = sum(
        item.get("classification") == "receipt_pending" for item in results
    )
    if summary.get("pending_receipts") != pending:
        findings.append(
            Finding(
                "examples/comparison.json",
                "pending receipt count must match result classifications",
            )
        )
    findings.extend(_validate_control_plane_examples(records))
    return findings


def _validate_control_plane_examples(records: dict[str, Any]) -> list[Finding]:
    """Check relationships that JSON Schema represents only within one record."""
    findings: list[Finding] = []

    horizon = records.get("coordination-horizon.json", {})
    work_items = horizon.get("work_items", [])
    work_ids = {item.get("item_id") for item in work_items}
    current_ids = set(horizon.get("current_item_ids", []))
    if not current_ids.issubset(work_ids):
        findings.append(
            Finding(
                "examples/coordination-horizon.json",
                "every current item must resolve to one declared work item",
            )
        )
    sequences = [item.get("sequence") for item in work_items]
    if len(sequences) != len(set(sequences)):
        findings.append(
            Finding(
                "examples/coordination-horizon.json",
                "work-item sequence values must be unique",
            )
        )

    probe = records.get("practitioner-probe.json", {})
    levels = sorted(
        item.get("level") for item in probe.get("proficiency_levels", [])
    )
    if levels != [1, 2, 3, 4, 5]:
        findings.append(
            Finding(
                "examples/practitioner-probe.json",
                "proficiency levels must represent the complete one-through-five ladder",
            )
        )

    caller = records.get("bounded-caller.json", {})
    operation = records.get("operation.json", {})
    approval = records.get("approval.json", {})
    effect = records.get("effect.json", {})
    call = records.get("call-receipt.json", {})
    operation_id = operation.get("operation_id")
    operation_version = operation.get("version")
    effect_class = operation.get("effect_class")
    if operation_id not in caller.get("permitted_operation_ids", []):
        findings.append(
            Finding(
                "examples/bounded-caller.json",
                "the example caller must permit the example operation",
            )
        )
    ceiling = caller.get("authority_ceiling")
    if (
        ceiling in EFFECT_CLASS_RANK
        and effect_class in EFFECT_CLASS_RANK
        and EFFECT_CLASS_RANK[ceiling] < EFFECT_CLASS_RANK[effect_class]
    ):
        findings.append(
            Finding(
                "examples/bounded-caller.json",
                "caller authority ceiling must cover the example operation effect",
            )
        )
    for label, record in (
        ("examples/approval.json", approval),
        ("examples/effect.json", effect),
        ("examples/call-receipt.json", call),
    ):
        if record.get("operation_id") != operation_id:
            findings.append(
                Finding(label, "operation identifier must match the operation example")
            )
        if record.get("operation_version") != operation_version:
            findings.append(
                Finding(label, "operation version must match the operation example")
            )
        if record.get("effect_class") != effect_class:
            findings.append(
                Finding(label, "effect class must match the operation example")
            )
    if call.get("caller_id") != caller.get("caller_id"):
        findings.append(
            Finding(
                "examples/call-receipt.json",
                "caller identifier must match the bounded-caller example",
            )
        )
    if approval.get("approval_id") not in call.get("approval_ids", []):
        findings.append(
            Finding(
                "examples/call-receipt.json",
                "authorized broad-write call must reference the approval example",
            )
        )
    if effect.get("effect_id") not in call.get("effect_ids", []):
        findings.append(
            Finding(
                "examples/call-receipt.json",
                "completed call must reference the effect example",
            )
        )
    if effect.get("call_id") != call.get("call_id"):
        findings.append(
            Finding(
                "examples/effect.json",
                "effect call identifier must match the call-receipt example",
            )
        )

    node = records.get("machine-node.json", {})
    first_receipt = records.get("first-receipt.json", {})
    if node.get("machine_node_id") != first_receipt.get("machine_node_id"):
        findings.append(
            Finding(
                "examples/first-receipt.json",
                "Machine Node identifier must match the orientation receipt",
            )
        )
    if node.get("first_receipt_contract_id") != first_receipt.get(
        "first_receipt_id"
    ):
        findings.append(
            Finding(
                "examples/machine-node.json",
                "first-receipt identifier must resolve to the orientation example",
            )
        )
    for label, record in (
        ("examples/machine-node.json", node),
        ("examples/first-receipt.json", first_receipt),
    ):
        if record.get("coordination_horizon_id") != horizon.get("horizon_id"):
            findings.append(
                Finding(label, "Coordination Horizon identifier must resolve")
            )

    closure = records.get("simulated-receipt-closure.json", {})
    receipt_closures = closure.get("receipt_closures", [])
    families = [item.get("family") for item in receipt_closures]
    if set(families) != SUBSTANTIVE_SIMULATED_RECEIPT_FAMILIES:
        findings.append(
            Finding(
                "examples/simulated-receipt-closure.json",
                "simulated closure must cover each substantive receipt family exactly once",
            )
        )
    if len(families) != len(set(families)):
        findings.append(
            Finding(
                "examples/simulated-receipt-closure.json",
                "simulated receipt families must be unique",
            )
        )
    acceptance_roles = {
        role
        for item in receipt_closures
        if item.get("family")
        == "accountable_scientific_quality_regulatory_acceptance"
        for role in item.get("modeled_authority_roles", [])
    }
    required_roles = {
        "Scientific authority",
        "Quality authority",
        "Regulatory authority",
    }
    if not required_roles.issubset(acceptance_roles):
        findings.append(
            Finding(
                "examples/simulated-receipt-closure.json",
                "simulated accountable acceptance must represent Scientific, Quality, and Regulatory authority roles",
            )
        )
    closure_artifact_ids = {
        artifact.get("artifact_id")
        for item in receipt_closures
        for artifact in item.get("artifacts", [])
    }
    check_artifact_ids = {
        artifact_id
        for check in closure.get("executable_checks", [])
        for artifact_id in check.get("artifact_ids", [])
    }
    if not closure_artifact_ids.issubset(check_artifact_ids):
        findings.append(
            Finding(
                "examples/simulated-receipt-closure.json",
                "each family closure artifact must be produced by an executable check",
            )
        )

    decision = records.get("decision.json", {})
    probability_horizon = decision.get("probability_horizon", {})
    if probability_horizon.get("ends_on", "") < probability_horizon.get(
        "begins_on", ""
    ):
        findings.append(
            Finding(
                "examples/decision.json",
                "probability horizon end must be on or after its beginning",
            )
        )
    return findings


def validate_repository_orientation() -> list[Finding]:
    """Validate root orientation records and their cross-record contract."""
    findings: list[Finding] = []
    records: dict[str, Any] = {}
    for document_name, schema_name in ROOT_ORIENTATION_SCHEMAS.items():
        document_path = ROOT / document_name
        try:
            record = load_json(document_path)
            records[document_name] = record
            for finding in SchemaValidator(SCHEMA_DIR / schema_name).validate(record):
                findings.append(
                    Finding(f"{document_name}{finding.path[1:]}", finding.message)
                )
        except (
            OSError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ) as exc:
            findings.append(Finding(document_name, str(exc)))

    if set(records) != set(ROOT_ORIENTATION_SCHEMAS):
        return findings
    findings.extend(_validate_repository_orientation_records(records))
    return findings


def _validate_repository_orientation_records(
    records: dict[str, Any],
) -> list[Finding]:
    """Check relationships across the root orientation and promotion records."""
    findings: list[Finding] = []
    node = records["machine-node.json"]
    first_receipt = records["first-receipt.json"]
    horizon = records["coordination-horizon.json"]
    promotion_receipt = records["promotion-receipt.json"]

    if node.get("machine_node_id") != first_receipt.get("machine_node_id"):
        findings.append(
            Finding(
                "first-receipt.json",
                "Machine Node identifier must match the root orientation node",
            )
        )
    if node.get("first_receipt_contract_id") != first_receipt.get(
        "first_receipt_id"
    ):
        findings.append(
            Finding(
                "machine-node.json",
                "first-receipt identifier must resolve to the root orientation receipt",
            )
        )
    for name, record in (
        ("machine-node.json", node),
        ("first-receipt.json", first_receipt),
    ):
        if record.get("coordination_horizon_id") != horizon.get("horizon_id"):
            findings.append(
                Finding(name, "Coordination Horizon identifier must resolve")
            )

    node_contracts = node.get("contracts", [])
    receipt_contracts = first_receipt.get("contract_state", [])
    if node_contracts != receipt_contracts:
        findings.append(
            Finding(
                "first-receipt.json.contract_state",
                "contract state must equal the Machine Node contract set",
            )
        )
    available_contracts = {
        item.get("contract_id"): item.get("version")
        for item in node_contracts
        if isinstance(item, dict)
    }
    if available_contracts != ROOT_ORIENTATION_CONTRACTS:
        findings.append(
            Finding(
                "machine-node.json.contracts",
                "root contracts must bind the selected-future closure and "
                "automation branch policy versions",
            )
        )
    for index, contract in enumerate(node_contracts):
        digest = contract.get("digest", "")
        if digest == ZERO_DIGEST:
            findings.append(
                Finding(
                    f"machine-node.json.contracts[{index}].digest",
                    "released contract references require a material digest",
                )
            )
        contract_id = contract.get("contract_id")
        material_path = ROOT_ORIENTATION_CONTRACT_FILES.get(contract_id)
        if material_path is not None:
            material_digest = f"sha256:{sha256(material_path.read_bytes()).hexdigest()}"
            if digest != material_digest:
                findings.append(
                    Finding(
                        f"machine-node.json.contracts[{index}].digest",
                        f"{contract_id} digest must bind "
                        f"{material_path.relative_to(ROOT)}",
                    )
                )

    if node.get("open_receipts") != first_receipt.get("open_receipts"):
        findings.append(
            Finding(
                "first-receipt.json.open_receipts",
                "open receipts must equal the Machine Node receipt set",
            )
        )
    promotion_receipt_id = promotion_receipt.get("promotion_receipt_id")
    if promotion_receipt_id != "RCP-GOVERNANCE-PROMOTION-002":
        findings.append(
            Finding(
                "promotion-receipt.json.promotion_receipt_id",
                "promotion receipt must use the governed repository receipt identity",
            )
        )
    if promotion_receipt.get("target_release") != "governance-v2.0.1":
        findings.append(
            Finding(
                "promotion-receipt.json.target_release",
                "promotion receipt must bind the canonical governance-v2.0.1 tag",
            )
        )

    campaigns = node.get("campaigns", [])
    campaign_ids = {
        item.get("campaign_id") for item in campaigns if isinstance(item, dict)
    }
    if campaign_ids != ROOT_ORIENTATION_CAMPAIGNS:
        findings.append(
            Finding(
                "machine-node.json.campaigns",
                "root orientation must mark all three constellation campaigns",
            )
        )
    for index, campaign in enumerate(campaigns):
        if campaign.get("marking_schema_version") != SCHEMA_RELEASE:
            findings.append(
                Finding(
                    f"machine-node.json.campaigns[{index}].marking_schema_version",
                    f"campaign markings must use schema release {SCHEMA_RELEASE}",
                )
            )

    work_items = horizon.get("work_items", [])
    work_ids = {
        item.get("item_id") for item in work_items if isinstance(item, dict)
    }
    current_ids = set(horizon.get("current_item_ids", []))
    if not current_ids.issubset(work_ids):
        findings.append(
            Finding(
                "coordination-horizon.json.current_item_ids",
                "every current item must resolve to a declared work item",
            )
        )
    sequences = [
        item.get("sequence") for item in work_items if isinstance(item, dict)
    ]
    if len(sequences) != len(set(sequences)):
        findings.append(
            Finding(
                "coordination-horizon.json.work_items",
                "work-item sequence values must be unique",
            )
        )
    for index, item in enumerate(work_items):
        missing_dependencies = set(item.get("dependency_ids", [])) - work_ids
        if missing_dependencies:
            findings.append(
                Finding(
                    f"coordination-horizon.json.work_items[{index}].dependency_ids",
                    "every dependency must resolve to a declared work item",
                )
            )

    provenance = node.get("current_provenance", {})
    zero_commit = provenance.get("commit") == ZERO_COMMIT
    zero_digest = provenance.get("digest") == ZERO_DIGEST
    if zero_commit != zero_digest:
        findings.append(
            Finding(
                "machine-node.json.current_provenance",
                "candidate commit and digest placeholders must settle together",
            )
        )
    if zero_commit and zero_digest:
        current_items = [
            item
            for item in work_items
            if item.get("item_id") in current_ids
        ]
        promotion_items = [
            item
            for item in current_items
            if "promotion"
            in " ".join(
                str(item.get(field, ""))
                for field in ("item_id", "horizon_label", "desired_state")
            ).lower()
        ]
        if node.get("lifecycle_state") != "settling":
            findings.append(
                Finding(
                    "machine-node.json.lifecycle_state",
                    "candidate provenance placeholders require a settling lifecycle",
                )
            )
        if not any(item.get("state") == "settling" for item in promotion_items):
            findings.append(
                Finding(
                    "coordination-horizon.json.current_item_ids",
                    "candidate provenance placeholders require a current settling "
                    "promotion item",
                )
            )
        if not node.get("open_receipts"):
            findings.append(
                Finding(
                    "machine-node.json.open_receipts",
                    "candidate provenance placeholders require an open promotion receipt",
                )
            )
        if promotion_receipt_id not in node.get("open_receipts", []):
            findings.append(
                Finding(
                    "machine-node.json.open_receipts",
                    "candidate provenance requires the concrete promotion receipt",
                )
            )
        if (
            promotion_receipt.get("promotion_state") != "candidate_pending"
            or promotion_receipt.get("release_coordinate") is not None
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json",
                    "candidate provenance requires a pending promotion receipt",
                )
            )
        if promotion_receipt.get("candidate_coordinate") != provenance:
            findings.append(
                Finding(
                    "promotion-receipt.json.candidate_coordinate",
                    "candidate promotion coordinates must equal Machine Node provenance",
                )
            )
    elif not zero_commit and not zero_digest:
        release_coordinate = promotion_receipt.get("release_coordinate")
        if node.get("lifecycle_state") not in {"reference_ready", "active"}:
            findings.append(
                Finding(
                    "machine-node.json.lifecycle_state",
                    "released provenance requires a reference-ready or active lifecycle",
                )
            )
        if promotion_receipt_id in node.get("open_receipts", []):
            findings.append(
                Finding(
                    "machine-node.json.open_receipts",
                    "released provenance requires the promotion receipt to be closed",
                )
            )
        if (
            promotion_receipt.get("promotion_state") != "released"
            or not isinstance(release_coordinate, dict)
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json",
                    "released provenance requires observed promotion evidence",
                )
            )
        elif (
            release_coordinate.get("commit") != provenance.get("commit")
            or release_coordinate.get("digest") != provenance.get("digest")
            or release_coordinate.get("tag") != provenance.get("release")
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json.release_coordinate",
                    "release evidence must equal Machine Node provenance",
                )
            )
        promotion_items = [
            item
            for item in work_items
            if "promotion"
            in " ".join(
                str(item.get(field, ""))
                for field in ("item_id", "horizon_label", "desired_state")
            ).lower()
        ]
        if not promotion_items or not all(
            item.get("state") == "complete" for item in promotion_items
        ):
            findings.append(
                Finding(
                    "coordination-horizon.json.work_items",
                    "released provenance requires completed promotion work",
                )
            )
    return findings


def validate_coordination_vocabulary() -> list[Finding]:
    """Keep the coordination abstraction independent of one time-bucket idiom."""
    findings: list[Finding] = []
    for path in sorted(ROOT.rglob("*")):
        if (
            path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path.suffix in {".json", ".md", ".yml", ".yaml", ".py"}
        ):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if LEGACY_COORDINATOR.search(line):
                    findings.append(
                        Finding(
                            f"{path.relative_to(ROOT)}:{line_number}",
                            "use the generic Coordination Horizon abstraction",
                        )
                    )
    return findings


def validate_rulesets() -> list[Finding]:
    """Check exported protections for the shared branch and release invariants."""
    findings: list[Finding] = []
    expected = {
        "main.json",
        "develop.json",
        "release-hotfix.json",
        "release-tags.json",
    }
    available = {path.name for path in RULESET_DIR.glob("*.json")}
    if available != expected:
        findings.append(
            Finding(
                "rulesets",
                f"ruleset catalog differs: expected {sorted(expected)}, "
                f"available {sorted(available)}",
            )
        )
    for path in sorted(RULESET_DIR.glob("*.json")):
        relative = str(path.relative_to(ROOT))
        try:
            ruleset = load_json(path)
        except (
            OSError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ) as exc:
            findings.append(Finding(relative, str(exc)))
            continue
        for key in ("name", "target", "enforcement", "conditions", "rules"):
            if key not in ruleset:
                findings.append(Finding(relative, f"ruleset requires {key!r}"))
        if ruleset.get("enforcement") != "active":
            findings.append(Finding(relative, "ruleset export should be active"))
        rules = ruleset.get("rules", [])
        rule_types = {rule.get("type") for rule in rules if isinstance(rule, dict)}
        for required_type in ("deletion", "non_fast_forward"):
            if required_type not in rule_types:
                findings.append(
                    Finding(relative, f"ruleset requires {required_type!r} protection")
                )
        if ruleset.get("target") == "branch":
            for required_type in ("pull_request", "required_status_checks"):
                if required_type not in rule_types:
                    findings.append(
                        Finding(
                            relative,
                            f"branch ruleset requires {required_type!r} protection",
                        )
                    )
            status_rules = [
                rule for rule in rules if rule.get("type") == "required_status_checks"
            ]
            contexts = {
                item.get("context")
                for rule in status_rules
                for item in rule.get("parameters", {}).get(
                    "required_status_checks", []
                )
            }
            required_contexts = {"branch-policy", "governance-validation"}
            missing_contexts = required_contexts - contexts
            if missing_contexts:
                findings.append(
                    Finding(
                        relative,
                        "branch ruleset is missing required status contexts: "
                        f"{sorted(missing_contexts)}",
                    )
                )
        if path.name in {"main.json", "release-hotfix.json", "release-tags.json"}:
            if "required_signatures" not in rule_types:
                findings.append(
                    Finding(relative, "production coordinates require signatures")
                )
        if path.name == "release-tags.json":
            includes = set(
                ruleset.get("conditions", {})
                .get("ref_name", {})
                .get("include", [])
            )
            if includes != RELEASE_TAG_INCLUDES:
                findings.append(
                    Finding(
                        relative,
                        "release tag coverage differs: "
                        f"expected {sorted(RELEASE_TAG_INCLUDES)}, "
                        f"available {sorted(includes)}",
                    )
                )
    return findings


def validate_workflows() -> list[Finding]:
    """Check workflow permissions and immutable third-party action coordinates."""
    findings: list[Finding] = []
    expected = {
        "branch-policy.yml",
        "validate.yml",
        "reusable-governance-validation.yml",
        "reusable-contract-validation.yml",
    }
    available = {path.name for path in WORKFLOW_DIR.glob("*.yml")}
    if available != expected:
        findings.append(
            Finding(
                ".github/workflows",
                f"workflow catalog differs: expected {sorted(expected)}, "
                f"available {sorted(available)}",
            )
        )
    action_reference = re.compile(r"^\s*uses:\s*([^#\s]+)", re.MULTILINE)
    immutable_action = re.compile(r"^[^@]+@[a-f0-9]{40}$")
    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        relative = str(path.relative_to(ROOT))
        content = path.read_text(encoding="utf-8")
        if "permissions:\n  contents: read" not in content:
            findings.append(
                Finding(relative, "workflow should declare read-only contents permission")
            )
        if path.name == "branch-policy.yml":
            required_policy_fragments = {
                "pull_request_target:": "branch policy requires base-context activation",
                "repository: ${{ github.repository }}": (
                    "branch policy checkout requires the base repository"
                ),
                "ref: ${{ github.event.pull_request.base.sha }}": (
                    "branch policy checkout requires the immutable pull-request base"
                ),
                "path: .branch-policy-base": (
                    "branch policy checkout requires its bounded static path"
                ),
                "sparse-checkout: tools/check_branch_flow.py": (
                    "branch policy checkout requires only the released checker"
                ),
                "sparse-checkout-cone-mode: false": (
                    "branch policy sparse checkout requires file-level selection"
                ),
                "working-directory: .branch-policy-base": (
                    "branch policy execution requires the bounded base checkout"
                ),
                "BASE_REF: ${{ github.event.pull_request.base.ref }}": (
                    "branch policy requires the event base branch"
                ),
                "HEAD_REF: ${{ github.event.pull_request.head.ref }}": (
                    "branch policy requires the event head branch as quoted data"
                ),
                "PR_AUTHOR: ${{ github.event.pull_request.user.login }}": (
                    "branch policy requires the event pull-request author"
                ),
                '--author "$PR_AUTHOR"': (
                    "branch policy requires quoted author binding"
                ),
            }
            for fragment, message in required_policy_fragments.items():
                if fragment not in content:
                    findings.append(Finding(relative, message))
            if content.count("actions/checkout@") != 1:
                findings.append(
                    Finding(
                        relative,
                        "branch policy requires exactly one base-controlled checkout",
                    )
                )
            if content.count(
                "${{ github.event.pull_request.head.ref }}"
            ) != 1:
                findings.append(
                    Finding(
                        relative,
                        "head branch data belongs only in the quoted checker argument",
                    )
                )
            for fragment in (
                "github.event.pull_request.head.sha",
                "git fetch ",
                "git checkout ",
                "gh pr checkout",
                "curl ",
                "wget ",
            ):
                if fragment in content:
                    findings.append(
                        Finding(
                            relative,
                            f"branch policy contains head-retrieval surface {fragment!r}",
                        )
                    )
        elif "pull_request_target:" in content:
            findings.append(
                Finding(
                    relative,
                    "pull_request_target authority belongs only to branch-policy.yml",
                )
            )
        if path.name == "reusable-contract-validation.yml":
            required_contract_fragments = {
                "driftframestudios/site-reading-governance)":
                    "governance repository requires an explicit allowlist",
                r"^[0-9a-f]{40}$":
                    "governance ref requires an immutable commit grammar",
                '"$GOVERNANCE_REF" == "0000000000000000000000000000000000000000"':
                    "governance ref requires explicit zero-placeholder rejection",
                "GOVERNANCE_REPOSITORY: ${{ inputs.governance_repository }}":
                    "repository input requires quoted environment projection",
                "GOVERNANCE_REF: ${{ inputs.governance_ref }}":
                    "ref input requires quoted environment projection",
            }
            for fragment, message in required_contract_fragments.items():
                if fragment not in content:
                    findings.append(Finding(relative, message))
        for reference in action_reference.findall(content):
            if reference.startswith("./"):
                continue
            if immutable_action.fullmatch(reference) is None:
                findings.append(
                    Finding(
                        relative,
                        f"action reference {reference!r} should use an immutable SHA",
                    )
                )
        checkout_count = content.count("actions/checkout@")
        credential_count = content.count("persist-credentials: false")
        if credential_count < checkout_count:
            findings.append(
                Finding(
                    relative,
                    "each checkout should preserve credentials in runner memory only",
                )
            )
    return findings


def validate_pair(schema_path: Path, document_path: Path) -> list[Finding]:
    """Validate one downstream document with one governance schema."""
    try:
        document = load_json(document_path)
        return SchemaValidator(schema_path).validate(document)
    except (
        OSError,
        json.JSONDecodeError,
        DuplicateKeyError,
        NonFiniteNumberError,
        ReferenceResolutionError,
    ) as exc:
        return [Finding(str(document_path), str(exc))]


def _contained_file(root: Path, relative_path: str, label: str) -> Path:
    """Resolve one existing relative file inside its declared root."""
    root_path = root.resolve(strict=True)
    candidate = (root_path / relative_path).resolve(strict=True)
    try:
        candidate.relative_to(root_path)
    except ValueError as exc:
        raise ContractInputError(f"{label} leaves its declared root") from exc
    if not candidate.is_file():
        raise ContractInputError(f"{label} resolves to a non-file path")
    return candidate


def validate_contract_request(
    governance_root: Path,
    source_root: Path,
    schema_name: str,
    document_path: str,
) -> list[Finding]:
    """Validate bounded reusable-workflow paths and the selected document."""
    try:
        if SCHEMA_NAME_PATTERN.fullmatch(schema_name) is None:
            raise ContractInputError(
                "schema name must be a direct lowercase *.schema.json filename"
            )
        if DOCUMENT_PATH_PATTERN.fullmatch(document_path) is None:
            raise ContractInputError(
                "document path must be a repository-relative JSON path"
            )
        schema_path = _contained_file(
            governance_root / "schemas",
            schema_name,
            "schema name",
        )
        resolved_document = _contained_file(
            source_root,
            document_path,
            "document path",
        )
    except (OSError, ContractInputError) as exc:
        return [Finding("contract-request", str(exc))]
    return validate_pair(schema_path, resolved_document)


def report(findings: Iterable[Finding]) -> int:
    """Render stable output for local and continuous-integration use."""
    materialized = list(findings)
    if materialized:
        print("Governance validation found contract differences:")
        for finding in materialized:
            print(f"  - {finding}")
        return 1
    print("Governance validation passed.")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--document", type=Path)
    parser.add_argument("--governance-root", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--schema-name")
    parser.add_argument("--document-path")
    args = parser.parse_args(argv)
    if (args.schema is None) != (args.document is None):
        parser.error("--schema and --document travel together")
    contract_values = (
        args.governance_root,
        args.source_root,
        args.schema_name,
        args.document_path,
    )
    if any(value is not None for value in contract_values) and any(
        value is None for value in contract_values
    ):
        parser.error(
            "--governance-root, --source-root, --schema-name, and "
            "--document-path travel together"
        )
    if args.schema is not None and args.schema_name is not None:
        parser.error("select either direct paths or a bounded contract request")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.schema:
        return report(validate_pair(args.schema, args.document))
    if args.schema_name:
        return report(
            validate_contract_request(
                args.governance_root,
                args.source_root,
                args.schema_name,
                args.document_path,
            )
        )
    return report(
        [
            *validate_schema_catalog(),
            *validate_examples(),
            *validate_repository_orientation(),
            *validate_rulesets(),
            *validate_workflows(),
            *validate_coordination_vocabulary(),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
