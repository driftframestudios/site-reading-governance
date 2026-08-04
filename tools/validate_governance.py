#!/usr/bin/env python3
"""Validate the small, documentary contract set with JSON Schema 2020-12."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXAMPLE_DIR = ROOT / "examples"

# TARGET: maintain the compact documentation surface below. Historical models stay
# available for provenance while active validation focuses on reusable artifacts.
ACTIVE_EXAMPLES = {
    "data-contract.json": "data-contract.schema.json",
    "database-refactor-finding.json": "database-refactor-finding.schema.json",
    "machine-node.json": "machine-node.schema.json",
    "practitioner-probe.json": "practitioner-probe.schema.json",
}

ROOT_DOCUMENTS = {
    "coordination-horizon.json": "coordination-horizon.schema.json",
    "machine-node.json": "machine-node.schema.json",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def schema_registry(schema_dir: Path = SCHEMA_DIR) -> Registry:
    resources = []
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def validate_document(
    document_path: Path,
    schema_path: Path,
    *,
    registry: Registry,
) -> list[str]:
    document = load_json(document_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    return [
        f"{document_path.name}:{error.json_path}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: item.json_path)
    ]


def validate_pairs(
    pairs: dict[str, str],
    *,
    document_dir: Path,
    schema_dir: Path = SCHEMA_DIR,
) -> list[str]:
    registry = schema_registry(schema_dir)
    findings: list[str] = []
    for document_name, schema_name in pairs.items():
        findings.extend(
            validate_document(
                document_dir / document_name,
                schema_dir / schema_name,
                registry=registry,
            )
        )
    return findings


def validate_examples() -> list[str]:
    return validate_pairs(ACTIVE_EXAMPLES, document_dir=EXAMPLE_DIR)


def validate_repository_orientation() -> list[str]:
    return validate_pairs(ROOT_DOCUMENTS, document_dir=ROOT)


def bounded_path(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    if root.resolve() not in candidate.parents:
        raise ValueError("path resolves outside the selected repository")
    return candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema")
    parser.add_argument("--document")
    parser.add_argument("--governance-root", default=str(ROOT))
    parser.add_argument("--source-root")
    parser.add_argument("--schema-name")
    parser.add_argument("--document-path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[str]

    if args.schema and args.document:
        schema_path = Path(args.schema).resolve()
        document_path = Path(args.document).resolve()
        findings = validate_document(
            document_path,
            schema_path,
            registry=schema_registry(schema_path.parent),
        )
    elif args.schema_name and args.document_path and args.source_root:
        governance_root = Path(args.governance_root).resolve()
        source_root = Path(args.source_root).resolve()
        schema_path = bounded_path(governance_root / "schemas", args.schema_name)
        document_path = bounded_path(source_root, args.document_path)
        findings = validate_document(
            document_path,
            schema_path,
            registry=schema_registry(governance_root / "schemas"),
        )
    elif any(
        value
        for value in (
            args.schema,
            args.document,
            args.source_root,
            args.schema_name,
            args.document_path,
        )
    ):
        raise SystemExit("provide one complete validation mode")
    else:
        findings = validate_examples() + validate_repository_orientation()

    if findings:
        print("Document validation found differences:")
        for finding in findings:
            print(f"  - {finding}")
        return 1

    print("Active documentary contracts validate with JSON Schema 2020-12.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
