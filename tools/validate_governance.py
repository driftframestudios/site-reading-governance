#!/usr/bin/env python3
"""Validate governance schemas, examples, references, and semantic invariants."""

from __future__ import annotations

import argparse
import datetime as dt
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
SCHEMA_RELEASE = "1.0.0"
SCHEMA_ID_PREFIX = "https://schemas.driftframe.org/site-reading-governance/v1.0/"
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
        findings.extend(_walk_references(schema, path, relative))
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
            if "governance-validation" not in contexts:
                findings.append(
                    Finding(
                        relative,
                        "branch ruleset requires governance-validation status",
                    )
                )
        if path.name in {"main.json", "release-tags.json"}:
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
            *validate_rulesets(),
            *validate_workflows(),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
