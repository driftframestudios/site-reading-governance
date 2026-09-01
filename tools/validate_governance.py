#!/usr/bin/env python3
"""Validate governance schemas, examples, references, and semantic invariants."""

from __future__ import annotations

import argparse
import datetime as dt
from hashlib import sha256
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urldefrag, urlsplit


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIRECTORY = Path(__file__).resolve().parent
if str(TOOL_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOL_DIRECTORY))

from automation_contract import (
    MISSING_AUTOMATION_CONTROLS,
    validate_repository_automation,
)
from build_governance_pages import (
    PUBLIC_SKILL_METADATA,
    PUBLIC_SKILL_SOURCE_PATH,
    PagesBuildError,
    parse_skill_source,
)


SCHEMA_DIR = ROOT / "schemas"
EXAMPLE_DIR = ROOT / "examples"
RULESET_DIR = ROOT / "rulesets"
WORKFLOW_DIR = ROOT / ".github" / "workflows"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_RELEASE = "2.1.0"
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
DATABASE_EXAMPLE_NAMES = {
    "data-contract.json",
    "database-refactor-finding.json",
    "database-migration-plan.json",
    "database-migration-receipt.json",
    "data-reconciliation.json",
    "database-release-manifest.json",
}
DATABASE_ACCEPTANCE_TYPES = {
    "scientific",
    "quality",
    "regulatory",
    "security_privacy",
    "operations",
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
    findings.extend(_validate_database_examples(records))
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


def _validate_database_examples(records: dict[str, Any]) -> list[Finding]:
    """Prove the database contract, plan, evidence, and release chain agrees."""
    if not DATABASE_EXAMPLE_NAMES.issubset(records):
        return []

    findings: list[Finding] = []
    contract = records["data-contract.json"]
    finding = records["database-refactor-finding.json"]
    plan = records["database-migration-plan.json"]
    receipt = records["database-migration-receipt.json"]
    reconciliation = records["data-reconciliation.json"]
    manifest = records["database-release-manifest.json"]

    contract_id = contract.get("data_contract_id")
    plan_id = plan.get("migration_plan_id")
    receipt_id = receipt.get("migration_receipt_id")
    reconciliation_id = reconciliation.get("reconciliation_id")

    for label, record in (
        ("examples/database-refactor-finding.json", finding),
        ("examples/database-migration-plan.json", plan),
        ("examples/database-migration-receipt.json", receipt),
        ("examples/data-reconciliation.json", reconciliation),
    ):
        if record.get("data_contract_id") != contract_id:
            findings.append(
                Finding(label, "data-contract identifier must resolve to the contract example")
            )

    entity_ids = [entity.get("entity_id") for entity in contract.get("entities", [])]
    if len(entity_ids) != len(set(entity_ids)):
        findings.append(
            Finding("examples/data-contract.json.entities", "entity identifiers must be unique")
        )
    entities = {
        entity.get("entity_id"): entity for entity in contract.get("entities", [])
    }
    engine_family = contract.get("database", {}).get("engine_family")
    for entity_index, entity in enumerate(contract.get("entities", [])):
        field_ids = [field.get("field_id") for field in entity.get("fields", [])]
        field_id_set = set(field_ids)
        if len(field_ids) != len(field_id_set):
            findings.append(
                Finding(
                    f"examples/data-contract.json.entities[{entity_index}].fields",
                    "field identifiers must be unique within one entity",
                )
            )
        if not set(entity.get("primary_key_field_ids", [])).issubset(field_id_set):
            findings.append(
                Finding(
                    f"examples/data-contract.json.entities[{entity_index}].primary_key_field_ids",
                    "every primary-key field must resolve within its entity",
                )
            )
        for field_index, field in enumerate(entity.get("fields", [])):
            physical_type = str(field.get("physical_type", "")).lower()
            semantic_type = field.get("semantic_type")
            expected_postgresql_type = {
                "instant": "timestamptz",
                "civil_date": "date",
                "boolean": "boolean",
            }.get(semantic_type)
            if (
                engine_family == "postgresql"
                and expected_postgresql_type is not None
                and physical_type != expected_postgresql_type
            ):
                findings.append(
                    Finding(
                        f"examples/data-contract.json.entities[{entity_index}]"
                        f".fields[{field_index}].physical_type",
                        f"PostgreSQL {semantic_type} fields use {expected_postgresql_type}",
                    )
                )
            if (
                engine_family == "postgresql"
                and semantic_type == "exact_decimal"
                and re.fullmatch(r"(?:numeric|decimal)\([1-9][0-9]*,[0-9]+\)", physical_type)
                is None
            ):
                findings.append(
                    Finding(
                        f"examples/data-contract.json.entities[{entity_index}]"
                        f".fields[{field_index}].physical_type",
                        "PostgreSQL exact-decimal fields use declared numeric precision and scale",
                    )
                )
        for constraint_index, constraint in enumerate(entity.get("constraints", [])):
            if not set(constraint.get("field_ids", [])).issubset(field_id_set):
                findings.append(
                    Finding(
                        f"examples/data-contract.json.entities[{entity_index}]"
                        f".constraints[{constraint_index}].field_ids",
                        "every constrained field must resolve within its entity",
                    )
                )
            if constraint.get("constraint_type") == "foreign_key":
                target = entities.get(constraint.get("referenced_entity_id"))
                if target is None:
                    findings.append(
                        Finding(
                            f"examples/data-contract.json.entities[{entity_index}]"
                            f".constraints[{constraint_index}].referenced_entity_id",
                            "foreign-key target entity must resolve",
                        )
                    )
                else:
                    target_field_ids = {
                        field.get("field_id") for field in target.get("fields", [])
                    }
                    if not set(constraint.get("referenced_field_ids", [])).issubset(
                        target_field_ids
                    ):
                        findings.append(
                            Finding(
                                f"examples/data-contract.json.entities[{entity_index}]"
                                f".constraints[{constraint_index}].referenced_field_ids",
                                "every foreign-key target field must resolve",
                            )
                        )

    if plan_id not in finding.get("target_migration_ids", []):
        findings.append(
            Finding(
                "examples/database-refactor-finding.json.target_migration_ids",
                "planned finding must reference the migration-plan example",
            )
        )

    phases = plan.get("phase_sequence", [])
    phase_ids = [phase.get("phase_id") for phase in phases]
    phase_sequences = [phase.get("sequence") for phase in phases]
    if len(phase_ids) != len(set(phase_ids)):
        findings.append(
            Finding(
                "examples/database-migration-plan.json.phase_sequence",
                "migration phase identifiers must be unique",
            )
        )
    if len(phase_sequences) != len(set(phase_sequences)):
        findings.append(
            Finding(
                "examples/database-migration-plan.json.phase_sequence",
                "migration phase sequence values must be unique",
            )
        )
    phase_sequence_by_id = {
        phase.get("phase_id"): phase.get("sequence") for phase in phases
    }
    for index, phase in enumerate(phases):
        for dependency_id in phase.get("dependency_phase_ids", []):
            dependency_sequence = phase_sequence_by_id.get(dependency_id)
            if dependency_sequence is None:
                findings.append(
                    Finding(
                        f"examples/database-migration-plan.json.phase_sequence[{index}]"
                        ".dependency_phase_ids",
                        "every phase dependency must resolve",
                    )
                )
            elif dependency_sequence >= phase.get("sequence", 0):
                findings.append(
                    Finding(
                        f"examples/database-migration-plan.json.phase_sequence[{index}]"
                        ".dependency_phase_ids",
                        "each phase dependency must precede its dependent phase",
                    )
                )
    if plan.get("recovery", {}).get("rollback_boundary_phase_id") not in set(phase_ids):
        findings.append(
            Finding(
                "examples/database-migration-plan.json.recovery.rollback_boundary_phase_id",
                "rollback boundary must resolve to one migration phase",
            )
        )

    receipt_matches = {
        "migration_plan_id": plan_id,
        "source_schema_digest": plan.get("source_schema_digest"),
        "target_schema_digest": plan.get("target_schema_digest"),
        "script_digest": plan.get("script", {}).get("digest"),
    }
    for field, expected in receipt_matches.items():
        if receipt.get(field) != expected:
            findings.append(
                Finding(
                    f"examples/database-migration-receipt.json.{field}",
                    f"{field.replace('_', ' ')} must match the migration plan",
                )
            )
    if receipt.get("tool_binding") != plan.get("tool_binding"):
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.tool_binding",
                "execution tool coordinate must match the migration plan",
            )
        )
    phase_results = receipt.get("phase_results", [])
    receipt_phase_ids = [result.get("phase_id") for result in phase_results]
    receipt_phase_sequences = [result.get("sequence") for result in phase_results]
    if set(receipt_phase_ids) != set(phase_ids) or len(receipt_phase_ids) != len(phase_ids):
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.phase_results",
                "execution receipt must cover every planned phase exactly once",
            )
        )
    if receipt_phase_sequences != phase_sequences:
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.phase_results",
                "execution receipt phase order must match the migration plan",
            )
        )
    maximum_planned_lock = max(
        (phase.get("lock_budget_milliseconds", 0) for phase in phases),
        default=0,
    )
    observed_lock = receipt.get("execution_metrics", {}).get(
        "maximum_lock_held_milliseconds",
        0,
    )
    if observed_lock > maximum_planned_lock:
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.execution_metrics"
                ".maximum_lock_held_milliseconds",
                "observed lock duration must remain within the planned phase budget",
            )
        )
    if receipt.get("outcome") == "passed" and any(
        result.get("outcome") != "passed" for result in phase_results
    ):
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.outcome",
                "passing execution requires a passing result for every phase",
            )
        )

    reconciliation_links = {
        "migration_receipt_id": receipt_id,
        "migration_plan_id": plan_id,
        "data_contract_id": contract_id,
    }
    for field, expected in reconciliation_links.items():
        if reconciliation.get(field) != expected:
            findings.append(
                Finding(
                    f"examples/data-reconciliation.json.{field}",
                    f"{field.replace('_', ' ')} must resolve to the evidence chain",
                )
            )
    if reconciliation_id not in receipt.get("reconciliation_ids", []):
        findings.append(
            Finding(
                "examples/database-migration-receipt.json.reconciliation_ids",
                "migration receipt must reference the reconciliation example",
            )
        )
    criteria = reconciliation.get("criteria", [])
    criterion_ids = [criterion.get("criterion_id") for criterion in criteria]
    if len(criterion_ids) != len(set(criterion_ids)):
        findings.append(
            Finding(
                "examples/data-reconciliation.json.criteria",
                "reconciliation criterion identifiers must be unique",
            )
        )
    if set(criterion_ids) != set(plan.get("verification_criteria", [])):
        findings.append(
            Finding(
                "examples/data-reconciliation.json.criteria",
                "reconciliation must implement every planned verification criterion",
            )
        )
    if reconciliation.get("overall_outcome") == "passed" and any(
        criterion.get("outcome") != "passed" for criterion in criteria
    ):
        findings.append(
            Finding(
                "examples/data-reconciliation.json.overall_outcome",
                "passing reconciliation requires a passing result for every criterion",
            )
        )
    for index, exception in enumerate(reconciliation.get("exceptions", [])):
        if exception.get("criterion_id") not in set(criterion_ids):
            findings.append(
                Finding(
                    f"examples/data-reconciliation.json.exceptions[{index}].criterion_id",
                    "exception criterion must resolve within the reconciliation",
                )
            )

    manifest_contract = manifest.get("data_contract", {})
    contract_matches = {
        "data_contract_id": contract_id,
        "version": contract.get("version"),
        "digest": contract.get("contract_digest"),
    }
    for field, expected in contract_matches.items():
        if manifest_contract.get(field) != expected:
            findings.append(
                Finding(
                    f"examples/database-release-manifest.json.data_contract.{field}",
                    "release manifest data-contract coordinate must match the contract example",
                )
            )
    migrations = manifest.get("ordered_migrations", [])
    migration_sequences = [item.get("sequence") for item in migrations]
    if len(migration_sequences) != len(set(migration_sequences)):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.ordered_migrations",
                "release migration sequence values must be unique",
            )
        )
    expected_sequences = list(range(1, len(migrations) + 1))
    if migration_sequences != expected_sequences:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.ordered_migrations",
                "release migrations must form one contiguous ordered chain",
            )
        )
    for previous, current in zip(migrations, migrations[1:]):
        if current.get("source_schema_digest") != previous.get(
            "applied_schema_digest"
        ):
            findings.append(
                Finding(
                    "examples/database-release-manifest.json.ordered_migrations",
                    "each migration source must equal the preceding applied schema",
                )
            )
    plan_entries = [item for item in migrations if item.get("migration_plan_id") == plan_id]
    if len(plan_entries) != 1:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.ordered_migrations",
                "release manifest must reference the migration plan exactly once",
            )
        )
    else:
        entry = plan_entries[0]
        entry_matches = {
            "migration_version": plan.get("version"),
            "script_digest": plan.get("script", {}).get("digest"),
            "source_schema_digest": plan.get("source_schema_digest"),
            "applied_schema_digest": plan.get("target_schema_digest"),
            "migration_receipt_id": receipt_id,
        }
        for field, expected in entry_matches.items():
            if entry.get(field) != expected:
                findings.append(
                    Finding(
                        f"examples/database-release-manifest.json.ordered_migrations.{field}",
                        f"manifest {field.replace('_', ' ')} must match the evidence chain",
                    )
                )
        if reconciliation_id not in entry.get("reconciliation_ids", []):
            findings.append(
                Finding(
                    "examples/database-release-manifest.json.ordered_migrations.reconciliation_ids",
                    "manifest migration must reference the reconciliation example",
                )
            )
    if manifest.get("current_schema_digest") != plan.get("target_schema_digest"):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.current_schema_digest",
                "release schema digest must equal the planned target schema digest",
            )
        )
    if migrations and manifest.get("current_schema_digest") != migrations[-1].get(
        "applied_schema_digest"
    ):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.current_schema_digest",
                "release schema digest must equal the final applied migration schema",
            )
        )
    baseline_support = [
        baseline
        for baseline in manifest.get("supported_upgrade_baselines", [])
        if baseline.get("schema_digest") == plan.get("source_schema_digest")
        and receipt_id in baseline.get("convergence_receipt_ids", [])
    ]
    if not baseline_support:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.supported_upgrade_baselines",
                "planned source schema must have a convergence receipt in the supported baselines",
            )
        )
    if receipt_id not in manifest.get("required_receipt_ids", []):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.required_receipt_ids",
                "release manifest must require the migration receipt",
            )
        )
    restore_ids = set(receipt.get("recovery_evidence", {}).get("restore_receipt_ids", []))
    if not restore_ids.issubset(set(manifest.get("required_receipt_ids", []))):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.required_receipt_ids",
                "release manifest must require every restore receipt",
            )
        )
    acceptance_bindings = manifest.get("acceptance_bindings", [])
    acceptance_types = [item.get("acceptance_type") for item in acceptance_bindings]
    if set(acceptance_types) != DATABASE_ACCEPTANCE_TYPES:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.acceptance_bindings",
                "database release must represent Scientific, Quality, Regulatory, Security, and Operations acceptance",
            )
        )
    if len(acceptance_types) != len(set(acceptance_types)):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.acceptance_bindings",
                "database release acceptance types must be unique",
            )
        )
    if manifest.get("evidence_mode") == "simulated" and any(
        binding.get("evidence_mode") != "simulated"
        or binding.get("status") != "projected"
        for binding in acceptance_bindings
    ):
        findings.append(
            Finding(
                "examples/database-release-manifest.json.acceptance_bindings",
                "simulated release acceptance remains projected with simulated evidence",
            )
        )
    unresolved_ids = set(manifest.get("unresolved_finding_ids", []))
    finding_status = finding.get("disposition", {}).get("status")
    finding_id = finding.get("finding_id")
    if finding_status in {"open", "planned"} and finding_id not in unresolved_ids:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.unresolved_finding_ids",
                "open and planned database findings must remain visible in the manifest",
            )
        )
    if finding_status in {"remediated", "accepted_by_design"} and finding_id in unresolved_ids:
        findings.append(
            Finding(
                "examples/database-release-manifest.json.unresolved_finding_ids",
                "settled database findings move out of the unresolved set",
            )
        )
    return findings


def validate_repository_orientation() -> list[Finding]:
    """Validate root orientation records and their cross-record contract."""
    findings: list[Finding] = []
    authors_path = ROOT / "AUTHORS"
    if not authors_path.is_file():
        findings.append(
            Finding("AUTHORS", "repository provenance requires its source-local carrier")
        )
    else:
        authors = authors_path.read_text(encoding="utf-8")
        if not authors.startswith("# General provenance\n"):
            findings.append(
                Finding("AUTHORS", "repository provenance requires its named carrier")
            )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "[`AUTHORS`](AUTHORS)" not in readme:
        findings.append(
            Finding("README.md", "repository orientation requires the AUTHORS route")
        )
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


def validate_public_ready_skills() -> list[Finding]:
    """Validate the exact repository-local skill accepted for public projection."""
    findings: list[Finding] = []
    skills_root = ROOT / ".agents" / "skills"
    public_paths: list[str] = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        relative = path.relative_to(ROOT).as_posix()
        try:
            metadata, content = parse_skill_source(path)
        except PagesBuildError as exc:
            findings.append(Finding(relative, str(exc)))
            continue
        if metadata.get("source_band") == "public_ready":
            public_paths.append(relative)
            normalized_content = " ".join(content.split())
            if metadata != PUBLIC_SKILL_METADATA:
                findings.append(
                    Finding(
                        relative,
                        "public-ready skill identity and upstream lineage must match "
                        "the accepted Governance collaboration guide",
                    )
                )
            if (
                "authorized resolver" not in normalized_content
                or "https://github.com/" in content
            ):
                findings.append(
                    Finding(
                        relative,
                        "public adaptation lineage must use its operator-blind key "
                        "and authorized resolver without a gated GitHub locator",
                    )
                )

    if public_paths != [PUBLIC_SKILL_SOURCE_PATH]:
        findings.append(
            Finding(
                ".agents/skills",
                "public-ready skill inventory must contain exactly "
                f"{PUBLIC_SKILL_SOURCE_PATH}",
            )
        )

    expected_route = f"[`{PUBLIC_SKILL_METADATA['name']}`]({PUBLIC_SKILL_SOURCE_PATH})"
    for orientation_path in ("README.md", "AGENTS.md"):
        path = ROOT / orientation_path
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(Finding(orientation_path, str(exc)))
            continue
        if expected_route not in content:
            findings.append(
                Finding(
                    orientation_path,
                    "repository orientation must link the exact public-ready skill path",
                )
            )
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
    if promotion_receipt.get("target_release") != "governance-v2.1.0":
        findings.append(
            Finding(
                "promotion-receipt.json.target_release",
                "promotion receipt must bind the canonical governance-v2.1.0 tag",
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
            promotion_receipt.get("promotion_state") != "candidate_ready"
            or promotion_receipt.get("release_coordinate") is not None
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json",
                    "candidate provenance requires a ready promotion receipt",
                )
            )
    elif not zero_commit and not zero_digest:
        release_coordinate = promotion_receipt.get("release_coordinate")
        if node.get("lifecycle_state") not in {"reference_ready", "active"}:
            findings.append(
                Finding(
                    "machine-node.json.lifecycle_state",
                    "observed release provenance requires a reference-ready or active lifecycle",
                )
            )
        if promotion_receipt_id in node.get("open_receipts", []):
            findings.append(
                Finding(
                    "machine-node.json.open_receipts",
                    "observed release provenance requires the promotion receipt to be closed",
                )
            )
        if (
            promotion_receipt.get("promotion_state") != "release_observed"
            or not isinstance(release_coordinate, dict)
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json",
                    "observed release provenance requires a release observation",
                )
            )
        elif (
            release_coordinate.get("commit_oid") != provenance.get("commit")
            or release_coordinate.get("archive_digest") != provenance.get("digest")
            or release_coordinate.get("tag") != provenance.get("release")
        ):
            findings.append(
                Finding(
                    "promotion-receipt.json.release_coordinate",
                    "release evidence must equal Machine Node provenance",
                )
            )
        if isinstance(release_coordinate, dict):
            if release_coordinate.get("tag") != promotion_receipt.get(
                "target_release"
            ):
                findings.append(
                    Finding(
                        "promotion-receipt.json.release_coordinate.tag",
                        "observed release tag must equal the receipt target release",
                    )
                )
            if not release_coordinate.get("local_proof_receipt"):
                findings.append(
                    Finding(
                        "promotion-receipt.json.release_coordinate.local_proof_receipt",
                        "observed release provenance requires the local proof receipt",
                    )
                )
            hosted_contexts = release_coordinate.get("hosted_check_contexts")
            if (
                isinstance(hosted_contexts, list)
                and hosted_contexts
                and not release_coordinate.get("hosted_automation_receipt")
            ):
                findings.append(
                    Finding(
                        "promotion-receipt.json.release_coordinate.hosted_automation_receipt",
                        "hosted proof contexts require a reviewed automation receipt",
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
                    "observed release provenance requires completed promotion work",
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
    """Check exported protections for main promotion and release tags."""
    findings: list[Finding] = []
    expected = {"main.json", "release-tags.json"}
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
            if "pull_request" not in rule_types:
                findings.append(
                    Finding(
                        relative,
                        "branch ruleset requires 'pull_request' protection",
                    )
                )
            if "required_status_checks" in rule_types:
                findings.append(
                    Finding(
                        relative,
                        "branch ruleset resting state keeps hosted status checks empty",
                    )
                )
            pull_request_rules = [
                rule
                for rule in rules
                if isinstance(rule, dict) and rule.get("type") == "pull_request"
            ]
            if len(pull_request_rules) == 1:
                parameters = pull_request_rules[0].get("parameters", {})
                expected_review_parameters = {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": True,
                    "require_last_push_approval": True,
                    "required_review_thread_resolution": True,
                    "allowed_merge_methods": ["merge", "squash"],
                }
                if parameters != expected_review_parameters:
                    findings.append(
                        Finding(
                            relative,
                            "pull-request protection must preserve one approval, "
                            "stale-review dismissal, CODEOWNER review, last-push "
                            "approval, thread resolution, and reviewed merge methods",
                        )
                    )
            elif pull_request_rules:
                findings.append(
                    Finding(relative, "branch ruleset requires one pull-request rule")
                )
        if path.name in {"main.json", "release-tags.json"}:
            if "required_signatures" not in rule_types:
                findings.append(
                    Finding(relative, "production coordinates require signatures")
                )
        if path.name == "main.json":
            includes = set(
                ruleset.get("conditions", {})
                .get("ref_name", {})
                .get("include", [])
            )
            if includes != {"refs/heads/main"}:
                findings.append(
                    Finding(
                        relative,
                        "main promotion protection requires the main branch coordinate",
                    )
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


def workflow_trigger_keys(workflow: str) -> set[str]:
    """Read exact top-level workflow triggers without adding a YAML dependency."""
    lines = workflow.splitlines()
    if "on:" not in lines:
        return set()
    start = lines.index("on:") + 1
    triggers: set[str] = set()
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        match = re.fullmatch(r"""  ["']?([A-Za-z0-9_-]+)["']?:.*""", line)
        if match:
            triggers.add(match.group(1))
    return triggers


def runner_job_blocks(workflow: str) -> dict[str, str]:
    """Return every workflow job that allocates a hosted runner."""
    lines = workflow.splitlines()
    if "jobs:" not in lines:
        return {}
    start = lines.index("jobs:") + 1
    job_starts = [
        (index, match.group(1))
        for index in range(start, len(lines))
        if (match := re.fullmatch(r"  ([A-Za-z0-9_-]+):", lines[index]))
    ]
    blocks: dict[str, str] = {}
    for position, (index, name) in enumerate(job_starts):
        end = (
            job_starts[position + 1][0]
            if position + 1 < len(job_starts)
            else len(lines)
        )
        block = "\n".join(lines[index:end])
        if re.search(r"(?m)^    runs-on:", block):
            blocks[name] = block
    return blocks


def validate_workflows() -> list[Finding]:
    """Check semantic automation contracts and immutable action coordinates."""
    findings: list[Finding] = []
    expected_triggers = {
        "pull-request.yml": {"pull_request"},
        "validate.yml": {"workflow_dispatch"},
        "reusable-governance-validation.yml": {"workflow_call"},
        "reusable-contract-validation.yml": {"workflow_call"},
    }
    workflow_paths = sorted(
        [*WORKFLOW_DIR.glob("*.yml"), *WORKFLOW_DIR.glob("*.yaml")]
    )
    available = {path.name for path in workflow_paths}
    if available != set(expected_triggers):
        findings.append(
            Finding(
                ".github/workflows",
                f"workflow catalog differs: expected {sorted(expected_triggers)}, "
                f"available {sorted(available)}",
            )
        )

    dependency_config = ROOT / ".github" / "dependabot.yml"
    dependency_content: str | None = None
    if not dependency_config.exists():
        findings.append(
            Finding(
                ".github/dependabot.yml",
                "monthly dependency upkeep requires its active configuration",
            )
        )
    else:
        dependency_content = dependency_config.read_text(encoding="utf-8")
    if (ROOT / ".github" / "dependabot.manual.yml").exists():
        findings.append(
            Finding(
                ".github/dependabot.manual.yml",
                "monthly dependency upkeep uses the active dependabot.yml source",
            )
        )

    automation_controls_path = ROOT / ".github" / "automation-controls.json"
    declared_controls: Any = MISSING_AUTOMATION_CONTROLS
    try:
        declared_controls = load_json(automation_controls_path)
    except (
        OSError,
        json.JSONDecodeError,
        DuplicateKeyError,
        NonFiniteNumberError,
    ) as exc:
        findings.append(Finding(".github/automation-controls.json", str(exc)))

    pull_request_path = WORKFLOW_DIR / "pull-request.yml"
    if dependency_content is not None and pull_request_path.exists():
        for message in validate_repository_automation(
            pull_request_path.read_text(encoding="utf-8"),
            dependency_content,
            declared_controls,
        ):
            findings.append(Finding(".github/workflows/pull-request.yml", message))

    codeowners_path = ROOT / ".github" / "CODEOWNERS"
    codeowners = (
        codeowners_path.read_text(encoding="utf-8")
        if codeowners_path.exists()
        else ""
    )
    if "/tools/automation_contract.py @driftframestudios" not in codeowners:
        findings.append(
            Finding(
                ".github/CODEOWNERS",
                "the semantic automation contract requires its source owner",
            )
        )
    if "/.github/automation-controls.json @driftframestudios" not in codeowners:
        findings.append(
            Finding(
                ".github/CODEOWNERS",
                "the automation controls projection requires its source owner",
            )
        )

    action_reference = re.compile(r"^\s*uses:\s*([^#\s]+)", re.MULTILINE)
    immutable_action = re.compile(r"^[^@]+@[a-f0-9]{40}$")
    for path in workflow_paths:
        relative = str(path.relative_to(ROOT))
        content = path.read_text(encoding="utf-8")
        if "permissions:\n  contents: read" not in content:
            findings.append(
                Finding(relative, "workflow should declare read-only contents permission")
            )
        triggers = workflow_trigger_keys(content)
        expected = expected_triggers.get(path.name, set())
        if triggers != expected:
            findings.append(
                Finding(
                    relative,
                    "workflow trigger allowlist differs: "
                    f"expected {sorted(expected)}, available {sorted(triggers)}",
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
        if path.name == "validate.yml":
            required_activation_fragments = {
                "workflow_dispatch:": (
                    "manual governance proof requires workflow_dispatch activation"
                ),
                "confirm_run:": (
                    "manual governance proof requires explicit human confirmation"
                ),
                "vars.ENABLE_GITHUB_ACTIONS == 'true'": (
                    "manual governance proof requires the repository-variable gate"
                ),
                "inputs.confirm_run": (
                    "manual governance proof requires the dispatch confirmation gate"
                ),
                "timeout-minutes: 10": (
                    "manual governance proof requires its bounded runner interval"
                ),
            }
            for fragment, message in required_activation_fragments.items():
                if fragment not in content:
                    findings.append(Finding(relative, message))
            runner_jobs = runner_job_blocks(content)
            if not runner_jobs:
                findings.append(
                    Finding(relative, "manual governance proof requires a runner job")
                )
            for name, block in runner_jobs.items():
                gate = re.search(r"(?m)^    if:\s*(.+)$", block)
                if gate is None or not all(
                    fragment in gate.group(1)
                    for fragment in (
                        "vars.ENABLE_GITHUB_ACTIONS == 'true'",
                        "inputs.confirm_run",
                    )
                ):
                    findings.append(
                        Finding(
                            relative,
                            f"manual workflow runner job {name!r} requires the "
                            "variable and confirmation gate",
                        )
                    )
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

    automation_note = (ROOT / ".github" / "AUTOMATION.md").read_text(
        encoding="utf-8"
    )
    required_automation_fragments = (
        "100–300 GitHub Actions runner\nminutes per month",
        "Pull requests targeting `develop` or `main`",
        "Superseded runs cancel",
        "## Deliberate full proof",
        "`ENABLE_GITHUB_ACTIONS=true`",
        "## Recovery",
        "`.github/dependabot.manual.yml` returns dependency scheduling",
    )
    for fragment in required_automation_fragments:
        if fragment not in automation_note:
            findings.append(
                Finding(
                    ".github/AUTOMATION.md",
                    "automation orientation requires the funded proof and recovery route: "
                    f"{fragment!r}",
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


def _run_git(repository_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    """Run one bounded Git observation without a shell."""
    return subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_stdout(
    repository_root: Path,
    arguments: tuple[str, ...],
    finding_path: str,
    failure_message: str,
) -> tuple[bytes | None, list[Finding]]:
    """Return Git output or one public-safe observation finding."""
    try:
        result = _run_git(repository_root, *arguments)
    except OSError:
        return None, [Finding(finding_path, "Git is unavailable for this observation")]
    if result.returncode != 0:
        return None, [Finding(finding_path, failure_message)]
    return result.stdout, []


def verify_release_coordinate(
    repository_root: Path,
    promotion_receipt_path: Path,
    carrier_ref: str = "HEAD",
) -> list[Finding]:
    """Verify an observed release subject from the later receipt carrier."""
    findings: list[Finding] = []
    try:
        resolved_repository = repository_root.resolve(strict=True)
        candidate_receipt = (
            promotion_receipt_path
            if promotion_receipt_path.is_absolute()
            else resolved_repository / promotion_receipt_path
        )
        resolved_receipt = candidate_receipt.resolve(strict=True)
        resolved_receipt.relative_to(resolved_repository)
        if not resolved_receipt.is_file():
            raise ContractInputError("promotion receipt resolves to a non-file path")
    except (OSError, ValueError, ContractInputError):
        return [
            Finding(
                "release-coordinate",
                "promotion receipt must be a readable file inside the Git repository",
            )
        ]

    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}", carrier_ref) is None
        or ".." in carrier_ref
        or "//" in carrier_ref
        or "@{" in carrier_ref
    ):
        return [
            Finding(
                "release-coordinate.carrier_ref",
                "carrier ref must use a bounded Git ref or object identifier",
            )
        ]

    try:
        receipt = load_json(resolved_receipt)
    except (
        OSError,
        json.JSONDecodeError,
        DuplicateKeyError,
        NonFiniteNumberError,
    ) as exc:
        return [Finding("release-coordinate.receipt", str(exc))]

    schema_findings = SchemaValidator(
        SCHEMA_DIR / "promotion-receipt.schema.json"
    ).validate(receipt)
    if schema_findings:
        return [
            Finding(f"promotion-receipt.json{item.path[1:]}", item.message)
            for item in schema_findings
        ]
    if receipt.get("promotion_state") != "release_observed":
        return [
            Finding(
                "promotion-receipt.json.promotion_state",
                "Git-backed verification begins after the release observation is recorded",
            )
        ]

    coordinate = receipt["release_coordinate"]
    if coordinate["tag"] != receipt["target_release"]:
        findings.append(
            Finding(
                "release-coordinate.tag",
                "observed release tag must equal the receipt target release",
            )
        )
    object_format_bytes, object_format_findings = _git_stdout(
        resolved_repository,
        ("rev-parse", "--show-object-format"),
        "release-coordinate.git_object_format",
        "Git object format could not be observed",
    )
    findings.extend(object_format_findings)
    if object_format_bytes is not None:
        observed_format = object_format_bytes.decode("ascii", errors="replace").strip()
        if coordinate["git_object_format"] != observed_format:
            findings.append(
                Finding(
                    "release-coordinate.git_object_format",
                    "recorded Git object format differs from the repository",
                )
            )

    tag_ref = f"refs/tags/{coordinate['tag']}"
    tag_type_bytes, tag_type_findings = _git_stdout(
        resolved_repository,
        ("cat-file", "-t", tag_ref),
        "release-coordinate.tag",
        "recorded release tag is unavailable",
    )
    findings.extend(tag_type_findings)
    if tag_type_bytes is not None and tag_type_bytes.strip() != b"tag":
        findings.append(
            Finding(
                "release-coordinate.tag",
                "release tag must be an annotated tag object",
            )
        )

    tag_oid_bytes, tag_oid_findings = _git_stdout(
        resolved_repository,
        ("rev-parse", "--verify", tag_ref),
        "release-coordinate.tag_object_oid",
        "release tag object identifier could not be resolved",
    )
    findings.extend(tag_oid_findings)
    if tag_oid_bytes is not None:
        observed_tag_oid = tag_oid_bytes.decode("ascii", errors="replace").strip()
        if coordinate["tag_object_oid"] != observed_tag_oid:
            findings.append(
                Finding(
                    "release-coordinate.tag_object_oid",
                    "recorded tag object identifier differs from the annotated tag",
                )
            )

    tag_commit_bytes, tag_commit_findings = _git_stdout(
        resolved_repository,
        ("rev-parse", "--verify", f"{tag_ref}^{{commit}}"),
        "release-coordinate.commit_oid",
        "release tag could not be dereferenced to a commit",
    )
    findings.extend(tag_commit_findings)
    if tag_commit_bytes is not None:
        observed_commit_oid = tag_commit_bytes.decode("ascii", errors="replace").strip()
        if coordinate["commit_oid"] != observed_commit_oid:
            findings.append(
                Finding(
                    "release-coordinate.commit_oid",
                    "recorded commit differs from the annotated tag subject",
                )
            )

    archive_bytes, archive_findings = _git_stdout(
        resolved_repository,
        ("archive", "--format=tar", coordinate["commit_oid"]),
        "release-coordinate.archive_digest",
        "accepted source could not be rendered as a Git tar archive",
    )
    findings.extend(archive_findings)
    if archive_bytes is not None:
        observed_digest = f"sha256:{sha256(archive_bytes).hexdigest()}"
        if coordinate["archive_digest"] != observed_digest:
            findings.append(
                Finding(
                    "release-coordinate.archive_digest",
                    "recorded archive digest differs from git archive --format=tar",
                )
            )

    carrier_oid_bytes, carrier_oid_findings = _git_stdout(
        resolved_repository,
        ("rev-parse", "--verify", f"{carrier_ref}^{{commit}}"),
        "release-coordinate.carrier_ref",
        "receipt carrier commit could not be resolved",
    )
    findings.extend(carrier_oid_findings)
    if carrier_oid_bytes is not None:
        carrier_oid = carrier_oid_bytes.decode("ascii", errors="replace").strip()
        if carrier_oid == coordinate["commit_oid"]:
            findings.append(
                Finding(
                    "release-coordinate.carrier_ref",
                    "receipt carrier must follow the tagged release subject",
                )
            )
        try:
            ancestry = _run_git(
                resolved_repository,
                "merge-base",
                "--is-ancestor",
                coordinate["commit_oid"],
                carrier_oid,
            )
        except OSError:
            findings.append(
                Finding(
                    "release-coordinate.carrier_ref",
                    "Git is unavailable for the ancestry observation",
                )
            )
        else:
            if ancestry.returncode == 1:
                findings.append(
                    Finding(
                        "release-coordinate.carrier_ref",
                        "tagged release subject must be an ancestor of the receipt carrier",
                    )
                )
            elif ancestry.returncode != 0:
                findings.append(
                    Finding(
                        "release-coordinate.carrier_ref",
                        "release-subject ancestry could not be observed",
                    )
                )

        relative_receipt = resolved_receipt.relative_to(resolved_repository).as_posix()
        carrier_receipt_bytes, carrier_receipt_findings = _git_stdout(
            resolved_repository,
            ("show", f"{carrier_oid}:{relative_receipt}"),
            "release-coordinate.carrier_ref",
            "receipt carrier does not contain the selected promotion receipt",
        )
        findings.extend(carrier_receipt_findings)
        if (
            carrier_receipt_bytes is not None
            and carrier_receipt_bytes != resolved_receipt.read_bytes()
        ):
            findings.append(
                Finding(
                    "release-coordinate.carrier_ref",
                    "working receipt bytes differ from the receipt carrier",
                )
            )
    return findings


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
    parser.add_argument("--verify-release-coordinate", action="store_true")
    parser.add_argument("--release-repository", type=Path)
    parser.add_argument("--promotion-receipt", type=Path)
    parser.add_argument("--carrier-ref", default="HEAD")
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
    if args.verify_release_coordinate and (
        args.schema is not None or args.schema_name is not None
    ):
        parser.error("select release-coordinate verification as its own observation")
    if not args.verify_release_coordinate and (
        args.release_repository is not None
        or args.promotion_receipt is not None
        or args.carrier_ref != "HEAD"
    ):
        parser.error(
            "--release-repository, --promotion-receipt, and --carrier-ref "
            "belong to --verify-release-coordinate"
        )
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.verify_release_coordinate:
        return report(
            verify_release_coordinate(
                args.release_repository or ROOT,
                args.promotion_receipt or Path("promotion-receipt.json"),
                args.carrier_ref,
            )
        )
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
            *validate_public_ready_skills(),
            *validate_rulesets(),
            *validate_workflows(),
            *validate_coordination_vocabulary(),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
