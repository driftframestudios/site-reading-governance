#!/usr/bin/env python3
"""Build and verify the bounded promotion-receipt schema projections."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterator, Mapping, Sequence
from urllib.parse import urldefrag, urlsplit

try:
    from graphql import build_ast_schema, parse, validate_schema
    from graphql.error import GraphQLError
    from graphql.language.ast import DirectiveDefinitionNode, DirectiveNode, Node
    from graphql.type import (
        GraphQLEnumType,
        GraphQLInputObjectType,
        GraphQLObjectType,
        GraphQLScalarType,
        GraphQLSchema,
        is_non_null_type,
    )
    from ruamel.yaml import YAML
    from ruamel.yaml.constructor import DuplicateKeyError as YamlDuplicateKeyError
    from ruamel.yaml.constructor import SafeConstructor
    from ruamel.yaml.events import AliasEvent
    from ruamel.yaml.parser import ParserError
    from ruamel.yaml.composer import ComposerError
    from ruamel.yaml.constructor import ConstructorError
except ImportError as exc:  # pragma: no cover - exercised by the dependency-free boundary
    raise SystemExit(
        "Schema projection dependencies are unavailable. Install the exact locked "
        "set with `python3 -m pip install --require-hashes "
        "-r requirements-projections.txt`."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA_PATH = "schemas/promotion-receipt.schema.json"
SOURCE_SCHEMA_ID = (
    "https://schemas.driftframe.org/site-reading-governance/v2.0/"
    "promotion-receipt.schema.json"
)
PROJECTION_ROOT = PurePosixPath(
    "schema-projections/promotion-receipt/v1.0.0"
)
GRAPHQL_SOURCE_PATH = (PROJECTION_ROOT / "promotion-receipt.graphql").as_posix()
COVERAGE_SOURCE_PATH = (PROJECTION_ROOT / "coverage.json").as_posix()
PROJECTION_VERSION = "1.0.0"
PROJECTION_OUTPUT_ROOT = PurePosixPath(
    "schemas/v2.0/projections/promotion-receipt/v1.0.0"
)
YAML_OUTPUT_PATH = (PROJECTION_OUTPUT_ROOT / "promotion-receipt.schema.yaml").as_posix()
GRAPHQL_OUTPUT_PATH = (PROJECTION_OUTPUT_ROOT / "promotion-receipt.graphql").as_posix()
COVERAGE_OUTPUT_PATH = (
    PROJECTION_OUTPUT_ROOT / "promotion-receipt.graphql-coverage.json"
).as_posix()
LEDGER_FIELDS = {
    "constraintTuples",
    "dispositionDefinitions",
    "family",
    "ledgerVersion",
    "projection",
    "source",
}
LEDGER_DISPOSITIONS = {
    "directly_mapped": (
        "The SDL carries the named field, object, input, list, enum, or reusable "
        "type relation. JSON Schema still validates instances."
    ),
    "outside_projection": (
        "The source constraint belongs to a concern outside this bounded interface."
    ),
    "represented_by_directive": (
        "An authored GraphQL directive carries the constraint as interface metadata."
    ),
    "retained_in_json_schema": (
        "JSON Schema retains the executable constraint while the SDL carries the "
        "adjacent interface shape."
    ),
}
ANNOTATION_KEYWORDS = {
    "$comment",
    "$id",
    "$schema",
    "default",
    "deprecated",
    "description",
    "examples",
    "readOnly",
    "title",
    "writeOnly",
}
RANGE_KEYWORDS = {
    "exclusiveMaximum",
    "exclusiveMinimum",
    "maxContains",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minContains",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "multipleOf",
}
GENERIC_CONSTRAINT_KINDS = {
    "contains": "containment",
    "dependentRequired": "dependent_required",
    "maxContains": "range",
    "minContains": "range",
    "not": "negated_schema",
    "patternProperties": "pattern_property",
    "propertyNames": "property_name_schema",
    "unevaluatedProperties": "unevaluated_properties",
}


class ProjectionError(ValueError):
    """Signal a deterministic projection or coverage-contract difference."""


class DuplicateJsonKeyError(ValueError):
    """Signal a duplicate key in a source or coverage JSON document."""


@dataclass(frozen=True, order=True)
class ConstraintTuple:
    """One exact, content-bound constraint in the reachable schema closure."""

    source_document: str
    source_pointer: str
    kind: str
    value_sha256: str

    def record(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "sourceDocument": self.source_document,
            "sourcePointer": self.source_pointer,
            "valueSha256": self.value_sha256,
        }


@dataclass(frozen=True)
class SourceGraphQLShape:
    """A GraphQL type expression derived from one JSON Schema value shape."""

    expression: str
    allows_null: bool

    def render(self, *, presence_required: bool) -> str:
        if presence_required and not self.allows_null:
            return f"{self.expression}!"
        return self.expression


def _object_with_unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON value {token!r}")


def load_json(path: Path) -> Any:
    """Read strict UTF-8 JSON with unique keys and finite numbers."""
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(
            text,
            object_pairs_hook=_object_with_unique_keys,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ProjectionError(f"{path} is not strict UTF-8 JSON: {exc}") from exc


def canonical_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for identity comparisons."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _stable_model(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable_model(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable_model(item) for item in value]
    return value


def _yaml_engine() -> YAML:
    yaml = YAML(typ="safe", pure=True)
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    yaml.allow_unicode = True
    yaml.default_flow_style = False
    yaml.explicit_start = True
    yaml.explicit_end = False
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.sort_base_mapping_type_on_output = True
    yaml.representer.ignore_aliases = lambda _value: True

    def quoted_string(representer: Any, value: str) -> Any:
        return representer.represent_scalar(
            "tag:yaml.org,2002:str",
            value,
            style='"',
        )

    yaml.representer.add_representer(str, quoted_string)
    yaml.Constructor.add_constructor(
        "tag:yaml.org,2002:timestamp",
        SafeConstructor.construct_yaml_str,
    )
    return yaml


def render_yaml_model(value: Any) -> bytes:
    """Render one stable YAML 1.2 document with every string quoted."""
    stream = io.StringIO(newline="\n")
    _yaml_engine().dump(_stable_model(value), stream)
    content = stream.getvalue().replace("\r\n", "\n").encode("utf-8")
    if not content.startswith(b"%YAML 1.2\n---\n") or not content.endswith(b"\n"):
        raise ProjectionError("generated YAML differs from the declared document profile")
    return content


def load_yaml_model(content: bytes) -> Any:
    """Parse one anchor-free YAML 1.2 document while preserving timestamp strings."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProjectionError("YAML projection is not UTF-8") from exc
    if "\r" in text:
        raise ProjectionError("YAML projection requires LF line endings")
    yaml = _yaml_engine()
    try:
        events = list(yaml.parse(text))
        for event in events:
            if isinstance(event, AliasEvent) or getattr(event, "anchor", None) is not None:
                raise ProjectionError("YAML projection carries an alias or anchor")
            if getattr(event, "tag", None) is not None:
                raise ProjectionError("YAML projection carries an explicit tag")
        value = yaml.load(text)
    except ProjectionError:
        raise
    except (
        ComposerError,
        ConstructorError,
        ParserError,
        YamlDuplicateKeyError,
        ValueError,
    ) as exc:
        raise ProjectionError(f"YAML projection is outside the declared profile: {exc}") from exc
    return value


def build_yaml_projection(root: Path = ROOT) -> bytes:
    source = load_json(root / SOURCE_SCHEMA_PATH)
    content = render_yaml_model(source)
    parsed = load_yaml_model(content)
    if canonical_json(parsed) != canonical_json(source):
        raise ProjectionError("YAML projection changes the JSON Schema data model")
    return content


def _pointer(parts: Sequence[str | int]) -> str:
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1")
        for part in parts
    )


def _decode_pointer(fragment: str) -> list[str]:
    if not fragment:
        return []
    if not fragment.startswith("/"):
        raise ProjectionError(f"schema reference fragment {fragment!r} is not a JSON Pointer")
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in fragment[1:].split("/")
    ]


def extract_constraint_tuples(root: Path = ROOT) -> tuple[ConstraintTuple, ...]:
    """Extract the exact reachable validation relations for the pilot family."""
    schema_root = (root / "schemas").resolve()
    document_cache: dict[Path, Any] = {}
    visited_nodes: set[tuple[Path, str]] = set()
    constraints: set[ConstraintTuple] = set()

    def load_document(path: Path) -> Any:
        resolved = path.resolve()
        try:
            resolved.relative_to(schema_root)
        except ValueError as exc:
            raise ProjectionError("schema reference leaves the bounded schema directory") from exc
        if resolved not in document_cache:
            document_cache[resolved] = load_json(resolved)
        return document_cache[resolved]

    def relative_document(path: Path) -> str:
        return path.resolve().relative_to(root.resolve()).as_posix()

    def add(path: Path, parts: Sequence[str | int], kind: str, value: Any) -> None:
        constraints.add(
            ConstraintTuple(
                source_document=relative_document(path),
                source_pointer=_pointer(parts),
                kind=kind,
                value_sha256=sha256_bytes(canonical_json(value)),
            )
        )

    def resolve_reference(path: Path, reference: str) -> tuple[Path, list[str], Any]:
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
            raise ProjectionError(f"schema reference {reference!r} leaves the local closure")
        target_path = (path.parent / relative).resolve() if location else path
        target = load_document(target_path)
        pointer_parts = _decode_pointer(fragment)
        try:
            for token in pointer_parts:
                target = target[token]
        except (KeyError, TypeError) as exc:
            raise ProjectionError(f"schema reference {reference!r} is unresolved") from exc
        return target_path, pointer_parts, target

    def walk(node: Any, path: Path, parts: list[str | int]) -> None:
        node_key = (path.resolve(), _pointer(parts))
        if node_key in visited_nodes:
            return
        visited_nodes.add(node_key)
        if isinstance(node, bool):
            add(path, parts, "boolean_schema", node)
            return
        if not isinstance(node, dict):
            raise ProjectionError(
                f"schema node {relative_document(path)}#{_pointer(parts)} must be an object or boolean"
            )

        recognized = set(ANNOTATION_KEYWORDS) | {"$defs"}
        if "$ref" in node:
            reference = node["$ref"]
            if not isinstance(reference, str):
                raise ProjectionError("schema $ref must be a string")
            add(path, [*parts, "$ref"], "reference", reference)
            target_path, target_parts, target = resolve_reference(path, reference)
            if len(target_parts) >= 2 and target_parts[-2] == "$defs":
                add(target_path, target_parts, "definition", target_parts[-1])
            walk(target, target_path, target_parts)
            recognized.add("$ref")

        if "type" in node:
            add(path, [*parts, "type"], "type", node["type"])
            recognized.add("type")
        if "additionalProperties" in node:
            add(
                path,
                [*parts, "additionalProperties"],
                "closure",
                node["additionalProperties"],
            )
            if isinstance(node["additionalProperties"], (dict, bool)) and node[
                "additionalProperties"
            ] is not False:
                walk(node["additionalProperties"], path, [*parts, "additionalProperties"])
            recognized.add("additionalProperties")

        if "properties" in node:
            properties = node["properties"]
            if not isinstance(properties, dict):
                raise ProjectionError("schema properties must be an object")
            for name, child in properties.items():
                add(path, [*parts, "properties", name], "property", name)
                walk(child, path, [*parts, "properties", name])
            recognized.add("properties")
        if "required" in node:
            required = node["required"]
            if not isinstance(required, list):
                raise ProjectionError("schema required must be an array")
            for index, name in enumerate(required):
                add(path, [*parts, "required", index], "required_relation", name)
            recognized.add("required")

        for keyword, kind in (
            ("const", "constant"),
            ("enum", "enum"),
            ("format", "format"),
            ("pattern", "pattern"),
            ("uniqueItems", "uniqueness"),
        ):
            if keyword in node:
                add(path, [*parts, keyword], kind, node[keyword])
                recognized.add(keyword)
        for keyword in RANGE_KEYWORDS:
            if keyword in node:
                add(path, [*parts, keyword], "range", node[keyword])
                recognized.add(keyword)

        for keyword in ("oneOf", "anyOf"):
            if keyword not in node:
                continue
            branches = node[keyword]
            if not isinstance(branches, list):
                raise ProjectionError(f"schema {keyword} must be an array")
            add(path, [*parts, keyword], "union", {"branches": len(branches)})
            for index, child in enumerate(branches):
                walk(child, path, [*parts, keyword, index])
            recognized.add(keyword)
        if "allOf" in node:
            branches = node["allOf"]
            if not isinstance(branches, list):
                raise ProjectionError("schema allOf must be an array")
            add(path, [*parts, "allOf"], "intersection", {"branches": len(branches)})
            for index, child in enumerate(branches):
                walk(child, path, [*parts, "allOf", index])
            recognized.add("allOf")
        if "items" in node:
            add(path, [*parts, "items"], "item_schema", True)
            walk(node["items"], path, [*parts, "items"])
            recognized.add("items")
        if "if" in node:
            conditional = {
                keyword: node[keyword]
                for keyword in ("if", "then", "else")
                if keyword in node
            }
            add(path, parts, "cross_field_constraint", conditional)
            walk(node["if"], path, [*parts, "if"])
            if "then" in node:
                walk(node["then"], path, [*parts, "then"])
            if "else" in node:
                walk(node["else"], path, [*parts, "else"])
            recognized.update(conditional)

        for keyword, kind in GENERIC_CONSTRAINT_KINDS.items():
            if keyword not in node:
                continue
            add(path, [*parts, keyword], kind, node[keyword])
            value = node[keyword]
            if keyword in {"contains", "not", "propertyNames", "unevaluatedProperties"}:
                walk(value, path, [*parts, keyword])
            recognized.add(keyword)

        unknown = set(node) - recognized
        if unknown:
            raise ProjectionError(
                f"coverage extraction needs a reviewed mapping for schema keywords {sorted(unknown)} "
                f"at {relative_document(path)}#{_pointer(parts)}"
            )

    source_path = (root / SOURCE_SCHEMA_PATH).resolve()
    source = load_document(source_path)
    if not isinstance(source, dict) or source.get("$id") != SOURCE_SCHEMA_ID:
        raise ProjectionError("promotion-receipt source identifier differs from the pilot")
    walk(source, source_path, [])
    return tuple(sorted(constraints))


def _field_coordinates(source_document: str, source_pointer: str) -> tuple[str, ...]:
    prefixes = (
        (
            SOURCE_SCHEMA_PATH,
            "/properties/release_coordinate/oneOf/1/properties/",
            "ReleaseCoordinate",
            "ReleaseCoordinateInput",
        ),
        (
            SOURCE_SCHEMA_PATH,
            "/properties/",
            "PromotionReceipt",
            "PromotionReceiptInput",
        ),
        (
            "schemas/common.schema.json",
            "/$defs/recordMetadata/properties/",
            "RecordMetadata",
            "RecordMetadataInput",
        ),
        (
            "schemas/common.schema.json",
            "/$defs/actor/properties/",
            "GovernanceActor",
            "GovernanceActorInput",
        ),
    )
    for document, prefix, output_type, input_type in prefixes:
        if source_document != document or not source_pointer.startswith(prefix):
            continue
        field = source_pointer[len(prefix) :]
        if field and "/" not in field:
            return (f"{output_type}.{field}", f"{input_type}.{field}")
    return ()


DEFINITION_COORDINATES = {
    ("schemas/common.schema.json", "/$defs/actor"): (
        "GovernanceActor",
        "GovernanceActorInput",
    ),
    ("schemas/common.schema.json", "/$defs/assuranceStage"): ("AssuranceStage",),
    ("schemas/common.schema.json", "/$defs/evidenceMode"): ("EvidenceMode",),
    ("schemas/common.schema.json", "/$defs/governedLocator"): ("GovernedLocator",),
    ("schemas/common.schema.json", "/$defs/identifier"): ("GovernanceIdentifier",),
    ("schemas/common.schema.json", "/$defs/recordMetadata"): (
        "RecordMetadata",
        "RecordMetadataInput",
    ),
    ("schemas/common.schema.json", "/$defs/semver"): ("SemanticVersion",),
}

ENUM_COORDINATES = {
    (SOURCE_SCHEMA_PATH, "/properties/promotion_state/enum"): ("PromotionState",),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/git_object_format/enum",
    ): ("GitObjectFormat",),
    ("schemas/common.schema.json", "/$defs/assuranceStage/enum"): ("AssuranceStage",),
    ("schemas/common.schema.json", "/$defs/evidenceMode/enum"): ("EvidenceMode",),
}

REQUIRED_PARENT_TYPES = {
    (SOURCE_SCHEMA_PATH, "/required/"): ("PromotionReceipt", "PromotionReceiptInput"),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/required/",
    ): ("ReleaseCoordinate", "ReleaseCoordinateInput"),
    ("schemas/common.schema.json", "/$defs/recordMetadata/required/"): (
        "RecordMetadata",
        "RecordMetadataInput",
    ),
    ("schemas/common.schema.json", "/$defs/actor/required/"): (
        "GovernanceActor",
        "GovernanceActorInput",
    ),
}
REQUIRED_NULLABLE_FIELDS = {
    (SOURCE_SCHEMA_PATH, "", "release_coordinate"),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1",
        "hosted_automation_receipt",
    ),
}


def _coverage_coordinates(
    item: ConstraintTuple,
    root: Path,
) -> tuple[str, ...]:
    key = (item.source_document, item.source_pointer)
    if item.kind == "property":
        return _field_coordinates(item.source_document, item.source_pointer)
    if item.kind == "reference" and item.source_pointer.endswith("/$ref"):
        return _field_coordinates(item.source_document, item.source_pointer[:-5])
    if item.kind == "definition":
        return DEFINITION_COORDINATES.get(key, ())
    if item.kind == "enum":
        return ENUM_COORDINATES.get(key, ())
    if item.kind == "required_relation":
        parts = _decode_pointer(item.source_pointer)
        if len(parts) < 2 or parts[-2] != "required":
            raise ProjectionError(
                f"required relation pointer needs a required array index: "
                f"{item.source_document}#{item.source_pointer}"
            )
        field_name = _source_pointer_value(
            root,
            item.source_document,
            item.source_pointer,
        )
        if not isinstance(field_name, str):
            raise ProjectionError(
                f"required relation needs a field name at "
                f"{item.source_document}#{item.source_pointer}"
            )
        parent_pointer = _pointer(parts[:-2])
        if (
            item.source_document,
            parent_pointer,
            field_name,
        ) in REQUIRED_NULLABLE_FIELDS:
            return ()
        for (document, prefix), types in REQUIRED_PARENT_TYPES.items():
            if item.source_document == document and item.source_pointer.startswith(prefix):
                return tuple(f"{type_name}.*" for type_name in types)
    return ()


def expected_coverage_ledger(root: Path = ROOT) -> dict[str, Any]:
    tuples = extract_constraint_tuples(root)
    reachable_documents = sorted(
        {SOURCE_SCHEMA_PATH, *(item.source_document for item in tuples)}
    )
    records: list[dict[str, Any]] = []
    for item in tuples:
        coordinates = _coverage_coordinates(item, root)
        record: dict[str, Any] = item.record()
        record["disposition"] = (
            "directly_mapped" if coordinates else "retained_in_json_schema"
        )
        record["graphqlCoordinates"] = list(coordinates)
        records.append(record)
    return {
        "constraintTuples": records,
        "dispositionDefinitions": LEDGER_DISPOSITIONS,
        "family": "promotion-receipt",
        "ledgerVersion": "1.0.0",
        "projection": {
            "format": "graphql-sdl",
            "path": GRAPHQL_SOURCE_PATH,
            "version": PROJECTION_VERSION,
        },
        "source": {
            "identifier": SOURCE_SCHEMA_ID,
            "reachableDocuments": reachable_documents,
            "rootDocument": SOURCE_SCHEMA_PATH,
        },
    }


def render_coverage_ledger(root: Path = ROOT) -> bytes:
    ledger = expected_coverage_ledger(root)
    records = ledger.pop("constraintTuples")
    lines = ["{", '  "constraintTuples": [']
    for index, record in enumerate(records):
        suffix = "," if index + 1 < len(records) else ""
        rendered = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ": "),
        )
        lines.append(f"    {rendered}{suffix}")
    lines.append("  ],")
    remainder = json.dumps(
        ledger,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).splitlines()
    lines.extend([f"  {line}" if line else line for line in remainder[1:-1]])
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _tuple_identity(record: Mapping[str, Any]) -> tuple[str, str, str, str]:
    fields = ("sourceDocument", "sourcePointer", "kind", "valueSha256")
    if not all(isinstance(record.get(field), str) for field in fields):
        raise ProjectionError("coverage ledger tuple identity requires four strings")
    return tuple(record[field] for field in fields)  # type: ignore[return-value]


def _source_pointer_value(
    root: Path,
    source_document: str,
    source_pointer: str,
) -> Any:
    document = load_json(root / source_document)
    pointer = source_pointer
    if not pointer:
        return document
    try:
        for decoded in _decode_pointer(pointer):
            document = document[int(decoded)] if isinstance(document, list) else document[decoded]
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ProjectionError(
            f"source pointer is unresolved: {source_document}#{pointer}"
        ) from exc
    return document


def _source_value(root: Path, record: Mapping[str, Any]) -> Any:
    return _source_pointer_value(
        root,
        str(record["sourceDocument"]),
        str(record["sourcePointer"]),
    )


def validate_coverage_ledger(
    root: Path = ROOT,
    *,
    ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    coverage_bytes: bytes | None = None
    if ledger is None:
        try:
            coverage_bytes = (root / COVERAGE_SOURCE_PATH).read_bytes()
        except OSError as exc:
            raise ProjectionError("coverage ledger must be readable") from exc
        observed = load_json(root / COVERAGE_SOURCE_PATH)
    else:
        observed = ledger
    if not isinstance(observed, dict) or set(observed) != LEDGER_FIELDS:
        raise ProjectionError("coverage ledger fields differ from the closed contract")
    records = observed.get("constraintTuples")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ProjectionError("coverage ledger constraintTuples must be an array of objects")
    identities = [_tuple_identity(item) for item in records]
    if len(identities) != len(set(identities)):
        raise ProjectionError("coverage ledger repeats a constraint tuple")
    expected = expected_coverage_ledger(root)
    expected_identities = {
        _tuple_identity(item) for item in expected["constraintTuples"]
    }
    observed_identities = set(identities)
    if observed_identities != expected_identities:
        missing = sorted(expected_identities - observed_identities)
        extra = sorted(observed_identities - expected_identities)
        raise ProjectionError(
            "coverage ledger and extracted constraint tuple sets differ; "
            f"missing={missing[:3]}, extra={extra[:3]}"
        )
    if observed != expected:
        raise ProjectionError("coverage ledger dispositions or GraphQL coordinates differ")
    if coverage_bytes is not None and coverage_bytes != render_coverage_ledger(root):
        raise ProjectionError("coverage ledger bytes differ from the deterministic form")
    return dict(observed)


EXPECTED_GRAPHQL_FIELDS = {
    "GovernanceActor": {
        "actor_id": "GovernanceIdentifier!",
        "display_name": "String!",
        "organization": "String",
        "role": "String!",
    },
    "GovernanceActorInput": {
        "actor_id": "GovernanceIdentifier!",
        "display_name": "String!",
        "organization": "String",
        "role": "String!",
    },
    "PromotionReceipt": {
        "accountable_role": "String!",
        "assurance_stage": "AssuranceStage!",
        "evidence_mode": "EvidenceMode!",
        "metadata": "RecordMetadata!",
        "promotion_receipt_id": "GovernanceIdentifier!",
        "promotion_state": "PromotionState!",
        "release_coordinate": "ReleaseCoordinate",
        "repository": "RepositoryCoordinate!",
        "required_evidence": "[String!]!",
        "target_release": "GovernanceReleaseTag!",
    },
    "PromotionReceiptInput": {
        "accountable_role": "String!",
        "assurance_stage": "AssuranceStage!",
        "evidence_mode": "EvidenceMode!",
        "metadata": "RecordMetadataInput!",
        "promotion_receipt_id": "GovernanceIdentifier!",
        "promotion_state": "PromotionState!",
        "release_coordinate": "ReleaseCoordinateInput",
        "repository": "RepositoryCoordinate!",
        "required_evidence": "[String!]!",
        "target_release": "GovernanceReleaseTag!",
    },
    "RecordMetadata": {
        "created_at": "DateTime!",
        "owner": "GovernanceActor!",
        "schema_version": "SemanticVersion!",
        "updated_at": "DateTime!",
    },
    "RecordMetadataInput": {
        "created_at": "DateTime!",
        "owner": "GovernanceActorInput!",
        "schema_version": "SemanticVersion!",
        "updated_at": "DateTime!",
    },
    "ReleaseCoordinate": {
        "archive_digest": "Sha256Digest!",
        "archive_format": "String!",
        "codeowner_resolution": "GovernedLocator!",
        "commit_oid": "GitObjectId!",
        "git_object_format": "GitObjectFormat!",
        "hosted_automation_receipt": "GovernedLocator",
        "hosted_check_contexts": "[String!]!",
        "local_proof_receipt": "GovernedLocator!",
        "promoted_at": "DateTime!",
        "ruleset_receipt": "GovernedLocator!",
        "tag": "GovernanceReleaseTag!",
        "tag_object_oid": "GitObjectId!",
        "tag_signature_receipt": "GovernedLocator!",
    },
    "ReleaseCoordinateInput": {
        "archive_digest": "Sha256Digest!",
        "archive_format": "String!",
        "codeowner_resolution": "GovernedLocator!",
        "commit_oid": "GitObjectId!",
        "git_object_format": "GitObjectFormat!",
        "hosted_automation_receipt": "GovernedLocator",
        "hosted_check_contexts": "[String!]!",
        "local_proof_receipt": "GovernedLocator!",
        "promoted_at": "DateTime!",
        "ruleset_receipt": "GovernedLocator!",
        "tag": "GovernanceReleaseTag!",
        "tag_object_oid": "GitObjectId!",
        "tag_signature_receipt": "GovernedLocator!",
    },
    "SchemaProjectionQuery": {
        "promotion_receipt": "PromotionReceipt",
    },
}
GRAPHQL_QUERY_ROOT_COORDINATE = "SchemaProjectionQuery.promotion_receipt"
EXPECTED_GRAPHQL_ENUMS = {
    "AssuranceStage": {
        "accepted",
        "qualified",
        "specified",
        "validated",
        "verified",
    },
    "EvidenceMode": {"observed", "planned", "simulated"},
    "GitObjectFormat": {"sha1", "sha256"},
    "PromotionState": {"candidate_ready", "release_observed"},
}
EXPECTED_GRAPHQL_INPUT_TYPES = {
    "GovernanceActorInput",
    "PromotionReceiptInput",
    "RecordMetadataInput",
    "ReleaseCoordinateInput",
}
EXPECTED_GRAPHQL_SCALARS = {
    "DateTime",
    "GitObjectId",
    "GovernanceIdentifier",
    "GovernedLocator",
    "RepositoryCoordinate",
    "SemanticVersion",
    "Sha256Digest",
    "GovernanceReleaseTag",
}
EXPECTED_GRAPHQL_DEFINITIONS = {
    ("schema_definition", None),
    *(
        (
            "input_object_type_definition"
            if name in EXPECTED_GRAPHQL_INPUT_TYPES
            else "object_type_definition",
            name,
        )
        for name in EXPECTED_GRAPHQL_FIELDS
    ),
    *(("enum_type_definition", name) for name in EXPECTED_GRAPHQL_ENUMS),
    *(("scalar_type_definition", name) for name in EXPECTED_GRAPHQL_SCALARS),
}

# JSON Schema expresses the underlying string or object shape while these
# authored bindings preserve the narrower interface meaning carried by the SDL.
# References and enums derive their names from their live source targets instead.
PROPERTY_NAMED_TYPE_BINDINGS = {
    (
        "schemas/common.schema.json",
        "/$defs/recordMetadata/properties/created_at",
    ): ("DateTime",),
    (
        "schemas/common.schema.json",
        "/$defs/recordMetadata/properties/updated_at",
    ): ("DateTime",),
    (SOURCE_SCHEMA_PATH, "/properties/release_coordinate"): (
        "ReleaseCoordinate",
        "ReleaseCoordinateInput",
    ),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/archive_digest",
    ): ("Sha256Digest",),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/commit_oid",
    ): ("GitObjectId",),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/promoted_at",
    ): ("DateTime",),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/tag",
    ): ("GovernanceReleaseTag",),
    (
        SOURCE_SCHEMA_PATH,
        "/properties/release_coordinate/oneOf/1/properties/tag_object_oid",
    ): ("GitObjectId",),
    (SOURCE_SCHEMA_PATH, "/properties/repository"): ("RepositoryCoordinate",),
    (SOURCE_SCHEMA_PATH, "/properties/target_release"): ("GovernanceReleaseTag",),
}

SCALAR_SOURCE_TYPES = {
    "Boolean": {"boolean"},
    "DateTime": {"string"},
    "Float": {"integer", "number"},
    "GitObjectId": {"string"},
    "GovernanceIdentifier": {"string"},
    "GovernanceReleaseTag": {"string"},
    "GovernedLocator": {"string"},
    "ID": {"integer", "string"},
    "Int": {"integer"},
    "RepositoryCoordinate": {"string"},
    "SemanticVersion": {"string"},
    "Sha256Digest": {"string"},
    "String": {"string"},
}


def _select_named_type(names: Sequence[str], coordinate: str) -> str:
    if len(names) == 1:
        return names[0]
    parent_type = coordinate.partition(".")[0]
    input_context = parent_type in EXPECTED_GRAPHQL_INPUT_TYPES
    candidates = [
        name
        for name in names
        if (name in EXPECTED_GRAPHQL_INPUT_TYPES) == input_context
    ]
    if len(candidates) != 1:
        raise ProjectionError(
            f"source binding for {coordinate} needs one matching GraphQL type"
        )
    return candidates[0]


def _resolve_source_reference(
    root: Path,
    source_document: str,
    reference: str,
) -> tuple[str, str, Any]:
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
        raise ProjectionError(f"schema reference {reference!r} leaves the local closure")
    current_path = (root / source_document).resolve()
    target_path = (current_path.parent / relative).resolve() if location else current_path
    schema_root = (root / "schemas").resolve()
    try:
        target_path.relative_to(schema_root)
        target_document = target_path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ProjectionError("schema reference leaves the bounded schema directory") from exc
    target_pointer = _pointer(_decode_pointer(fragment))
    target = _source_pointer_value(root, target_document, target_pointer)
    return target_document, target_pointer, target


def _split_source_nullability(
    node: Mapping[str, Any],
    *,
    source_document: str,
    source_pointer: str,
) -> tuple[bool, Mapping[str, Any]]:
    branches = node.get("oneOf")
    if branches is not None:
        if not isinstance(branches, list):
            raise ProjectionError(
                f"source field shape needs an array at {source_document}#{source_pointer}/oneOf"
            )
        null_branches = [
            branch
            for branch in branches
            if isinstance(branch, dict) and branch.get("type") == "null"
        ]
        value_branches = [branch for branch in branches if branch not in null_branches]
        if (
            len(null_branches) != 1
            or len(value_branches) != 1
            or not isinstance(value_branches[0], dict)
        ):
            raise ProjectionError(
                "GraphQL source binding supports one value shape with an optional null branch "
                f"at {source_document}#{source_pointer}"
            )
        return True, value_branches[0]

    source_type = node.get("type")
    if isinstance(source_type, list):
        if not all(isinstance(item, str) for item in source_type):
            raise ProjectionError(
                f"source field type names need strings at {source_document}#{source_pointer}"
            )
        value_types = [item for item in source_type if item != "null"]
        if "null" not in source_type or len(value_types) != 1:
            raise ProjectionError(
                "GraphQL source binding supports one value type with optional nullability "
                f"at {source_document}#{source_pointer}"
            )
        normalized = dict(node)
        normalized["type"] = value_types[0]
        return True, normalized
    return source_type == "null", node


def _assert_named_source_shape(
    schema: GraphQLSchema,
    name: str,
    node: Mapping[str, Any],
    *,
    source_document: str,
    source_pointer: str,
) -> bool:
    allows_null, core = _split_source_nullability(
        node,
        source_document=source_document,
        source_pointer=source_pointer,
    )
    source_type = core.get("type")
    graphql_type = schema.get_type(name)
    if isinstance(graphql_type, GraphQLEnumType):
        values = core.get("enum")
        if (
            source_type != "string"
            or not isinstance(values, list)
            or not all(isinstance(value, str) for value in values)
            or len(values) != len(set(values))
        ):
            raise ProjectionError(
                f"GraphQL enum {name} needs one unique string value set from "
                f"{source_document}#{source_pointer}"
            )
        observed_values = set(graphql_type.values)
        source_values = set(values)
        if observed_values != source_values:
            raise ProjectionError(
                f"GraphQL enum {name} values need to match the source; "
                f"source={sorted(source_values)}, GraphQL={sorted(observed_values)}"
            )
    elif isinstance(graphql_type, GraphQLScalarType):
        expected_source_types = SCALAR_SOURCE_TYPES.get(name)
        if expected_source_types is None or source_type not in expected_source_types:
            raise ProjectionError(
                f"GraphQL scalar {name} needs a compatible source type at "
                f"{source_document}#{source_pointer}; source carries {source_type!r}"
            )
    elif isinstance(graphql_type, (GraphQLObjectType, GraphQLInputObjectType)):
        if source_type != "object":
            raise ProjectionError(
                f"GraphQL object {name} needs an object source at "
                f"{source_document}#{source_pointer}; source carries {source_type!r}"
            )
    else:
        raise ProjectionError(f"GraphQL source binding type is unavailable: {name}")
    return allows_null


def _derive_source_graphql_shape(
    root: Path,
    schema: GraphQLSchema,
    source_document: str,
    source_pointer: str,
    coordinate: str,
) -> SourceGraphQLShape:
    node = _source_pointer_value(root, source_document, source_pointer)
    if not isinstance(node, dict):
        raise ProjectionError(
            "directly mapped source field needs an object schema at "
            f"{source_document}#{source_pointer}"
        )
    allows_null, core = _split_source_nullability(
        node,
        source_document=source_document,
        source_pointer=source_pointer,
    )
    if core.get("type") == "null":
        raise ProjectionError(
            "directly mapped source field needs a value shape at "
            f"{source_document}#{source_pointer}"
        )

    reference = core.get("$ref")
    if reference is not None:
        if not isinstance(reference, str):
            raise ProjectionError(
                f"source reference needs a string at {source_document}#{source_pointer}"
            )
        target_document, target_pointer, target = _resolve_source_reference(
            root,
            source_document,
            reference,
        )
        names = DEFINITION_COORDINATES.get((target_document, target_pointer))
        if names is None or not isinstance(target, dict):
            raise ProjectionError(
                "directly mapped source reference needs a reviewed GraphQL target: "
                f"{target_document}#{target_pointer}"
            )
        name = _select_named_type(names, coordinate)
        target_allows_null = _assert_named_source_shape(
            schema,
            name,
            target,
            source_document=target_document,
            source_pointer=target_pointer,
        )
        return SourceGraphQLShape(name, allows_null or target_allows_null)

    enum_key = (source_document, f"{source_pointer}/enum")
    if "enum" in core:
        names = ENUM_COORDINATES.get(enum_key)
        if names is None:
            raise ProjectionError(
                "directly mapped source enum needs a reviewed GraphQL target: "
                f"{source_document}#{source_pointer}"
            )
        name = _select_named_type(names, coordinate)
        _assert_named_source_shape(
            schema,
            name,
            core,
            source_document=source_document,
            source_pointer=source_pointer,
        )
        return SourceGraphQLShape(name, allows_null)

    source_type = core.get("type")
    if source_type == "array":
        items_pointer = f"{source_pointer}/items"
        if not isinstance(core.get("items"), dict):
            raise ProjectionError(
                "directly mapped list needs one item schema at "
                f"{source_document}#{items_pointer}"
            )
        item_shape = _derive_source_graphql_shape(
            root,
            schema,
            source_document,
            items_pointer,
            coordinate,
        )
        return SourceGraphQLShape(
            f"[{item_shape.render(presence_required=True)}]",
            allows_null,
        )

    named_types = PROPERTY_NAMED_TYPE_BINDINGS.get(
        (source_document, source_pointer)
    )
    if named_types is not None:
        name = _select_named_type(named_types, coordinate)
        _assert_named_source_shape(
            schema,
            name,
            core,
            source_document=source_document,
            source_pointer=source_pointer,
        )
        return SourceGraphQLShape(name, allows_null)

    primitive_names = {
        "boolean": "Boolean",
        "integer": "Int",
        "number": "Float",
        "string": "String",
    }
    name = primitive_names.get(source_type)
    if name is None:
        raise ProjectionError(
            "directly mapped source field needs a reviewed GraphQL shape at "
            f"{source_document}#{source_pointer}; source carries {source_type!r}"
        )
    return SourceGraphQLShape(name, allows_null)


def _source_property_required(
    root: Path,
    source_document: str,
    source_pointer: str,
) -> bool:
    parts = _decode_pointer(source_pointer)
    if len(parts) < 2 or parts[-2] != "properties":
        raise ProjectionError(
            "directly mapped property pointer needs a properties segment: "
            f"{source_document}#{source_pointer}"
        )
    parent_pointer = _pointer(parts[:-2])
    parent = _source_pointer_value(root, source_document, parent_pointer)
    required = parent.get("required", []) if isinstance(parent, dict) else None
    if not isinstance(required, list) or not all(
        isinstance(name, str) for name in required
    ):
        raise ProjectionError(
            "source required list needs field names at "
            f"{source_document}#{parent_pointer or '/'}"
        )
    return parts[-1] in required


def _validate_graphql_source_bindings(
    root: Path,
    schema: GraphQLSchema,
    coverage: Mapping[str, Any],
) -> None:
    records = coverage.get("constraintTuples")
    if not isinstance(records, list):
        raise ProjectionError("source binding needs the extracted coverage records")
    property_records = [
        record
        for record in records
        if record.get("kind") == "property"
        and record.get("disposition") == "directly_mapped"
    ]
    direct_keys = {
        (str(record["sourceDocument"]), str(record["sourcePointer"]))
        for record in property_records
    }
    authored_fields = {
        f"{type_name}.{field_name}"
        for type_name, fields in EXPECTED_GRAPHQL_FIELDS.items()
        for field_name in fields
    }
    if GRAPHQL_QUERY_ROOT_COORDINATE not in authored_fields:
        raise ProjectionError("GraphQL query-root source exception needs its authored field")
    projected_fields = authored_fields - {GRAPHQL_QUERY_ROOT_COORDINATE}
    mapped_source_fields = {
        str(coordinate)
        for record in property_records
        for coordinate in record.get("graphqlCoordinates", [])
    }
    unbound_fields = sorted(projected_fields - mapped_source_fields)
    if unbound_fields:
        raise ProjectionError(
            "GraphQL projection fields need directly mapped source properties: "
            f"{unbound_fields}"
        )
    stale_named_bindings = set(PROPERTY_NAMED_TYPE_BINDINGS) - direct_keys
    if stale_named_bindings:
        raise ProjectionError(
            "GraphQL named source bindings need current property coordinates: "
            f"{sorted(stale_named_bindings)}"
        )

    for record in property_records:
        source_document = str(record["sourceDocument"])
        source_pointer = str(record["sourcePointer"])
        presence_required = _source_property_required(
            root,
            source_document,
            source_pointer,
        )
        coordinates = record.get("graphqlCoordinates")
        if not isinstance(coordinates, list) or not coordinates:
            raise ProjectionError(
                "directly mapped property needs a GraphQL coordinate: "
                f"{source_document}#{source_pointer}"
            )
        for coordinate in coordinates:
            type_name, separator, field_name = str(coordinate).partition(".")
            type_definition = schema.get_type(type_name)
            if not separator or not isinstance(
                type_definition,
                (GraphQLObjectType, GraphQLInputObjectType),
            ):
                raise ProjectionError(
                    f"directly mapped property needs a GraphQL field: {coordinate}"
                )
            field = type_definition.fields.get(field_name)
            if field is None:
                raise ProjectionError(f"GraphQL field is absent: {coordinate}")
            source_shape = _derive_source_graphql_shape(
                root,
                schema,
                source_document,
                source_pointer,
                str(coordinate),
            )
            expected_type = source_shape.render(presence_required=presence_required)
            observed_type = str(field.type)
            if observed_type != expected_type:
                raise ProjectionError(
                    f"GraphQL field {coordinate} needs type {expected_type} to match "
                    f"{source_document}#{source_pointer}; GraphQL carries {observed_type}"
                )


def _walk_graphql_ast(value: Any) -> Iterator[Node]:
    """Yield every GraphQL AST node for closed directive-use inspection."""
    if isinstance(value, Node):
        yield value
        for key in value.keys:
            yield from _walk_graphql_ast(getattr(value, key, None))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_graphql_ast(item)


def validate_graphql_projection(root: Path = ROOT) -> bytes:
    path = root / GRAPHQL_SOURCE_PATH
    try:
        content = path.read_bytes()
        source = content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ProjectionError(f"{GRAPHQL_SOURCE_PATH} must be readable UTF-8") from exc
    if "\r" in source or not source.endswith("\n"):
        raise ProjectionError("GraphQL SDL requires LF line endings and a final newline")
    try:
        document = parse(source)
        if any(isinstance(item, DirectiveDefinitionNode) for item in document.definitions):
            raise ProjectionError("the pilot SDL keeps executable constraints in JSON Schema")
        observed_definitions = [
            (
                definition.kind,
                definition.name.value
                if getattr(definition, "name", None) is not None
                else None,
            )
            for definition in document.definitions
        ]
        if (
            len(observed_definitions) != len(set(observed_definitions))
            or set(observed_definitions) != EXPECTED_GRAPHQL_DEFINITIONS
        ):
            raise ProjectionError("GraphQL authored definition inventory differs")
        if any(isinstance(node, DirectiveNode) for node in _walk_graphql_ast(document)):
            raise ProjectionError("GraphQL authored directive use extends beyond the pilot")
        schema = build_ast_schema(document)
        errors = validate_schema(schema)
    except GraphQLError as exc:
        raise ProjectionError(f"GraphQL SDL does not parse and compose: {exc}") from exc
    if errors:
        raise ProjectionError(f"GraphQL SDL does not compose: {errors[0]}")
    if schema.query_type is None or schema.query_type.name != "SchemaProjectionQuery":
        raise ProjectionError("GraphQL SDL requires its bounded inspection query root")
    if schema.mutation_type is not None or schema.subscription_type is not None:
        raise ProjectionError("GraphQL SDL extends beyond the read-only inspection posture")

    for type_name, expected_fields in EXPECTED_GRAPHQL_FIELDS.items():
        type_definition = schema.get_type(type_name)
        expected_kind = (
            GraphQLInputObjectType
            if type_name in EXPECTED_GRAPHQL_INPUT_TYPES
            else GraphQLObjectType
        )
        if not isinstance(type_definition, expected_kind):
            raise ProjectionError(f"GraphQL type {type_name} is absent or has the wrong kind")
        observed_fields = {
            name: str(field.type) for name, field in type_definition.fields.items()
        }
        if observed_fields != expected_fields:
            raise ProjectionError(f"GraphQL fields differ for {type_name}")
    for type_name, expected_values in EXPECTED_GRAPHQL_ENUMS.items():
        type_definition = schema.get_type(type_name)
        if not isinstance(type_definition, GraphQLEnumType):
            raise ProjectionError(f"GraphQL enum {type_name} is absent")
        if set(type_definition.values) != expected_values:
            raise ProjectionError(f"GraphQL enum values differ for {type_name}")

    coverage = expected_coverage_ledger(root)
    _validate_graphql_source_bindings(root, schema, coverage)

    declared_coordinates = {
        coordinate
        for item in coverage["constraintTuples"]
        for coordinate in item["graphqlCoordinates"]
    }
    for coordinate in declared_coordinates:
        type_name, separator, field_name = coordinate.partition(".")
        type_definition = schema.get_type(type_name)
        if type_definition is None:
            raise ProjectionError(f"coverage ledger GraphQL type is absent: {type_name}")
        if not separator:
            continue
        if not isinstance(type_definition, (GraphQLObjectType, GraphQLInputObjectType)):
            raise ProjectionError(f"coverage ledger coordinate is not a field: {coordinate}")
        if field_name == "*":
            matching_records = [
                item
                for item in coverage["constraintTuples"]
                if coordinate in item["graphqlCoordinates"]
            ]
            for item in matching_records:
                required_name = _source_value(root, item)
                field = type_definition.fields.get(required_name)
                if field is None or not is_non_null_type(field.type):
                    raise ProjectionError(
                        f"GraphQL required field differs for {type_name}.{required_name}"
                    )
            continue
        if field_name not in type_definition.fields:
            raise ProjectionError(f"coverage ledger GraphQL field is absent: {coordinate}")
    return content


def projection_artifacts(root: Path = ROOT) -> dict[str, bytes]:
    """Return the validated deterministic output bytes for the pilot family."""
    yaml_content = build_yaml_projection(root)
    graphql_content = validate_graphql_projection(root)
    validate_coverage_ledger(root)
    coverage_content = (root / COVERAGE_SOURCE_PATH).read_bytes()
    return {
        YAML_OUTPUT_PATH: yaml_content,
        GRAPHQL_OUTPUT_PATH: graphql_content,
        COVERAGE_OUTPUT_PATH: coverage_content,
    }


def validate_projections(root: Path = ROOT) -> None:
    source = load_json(root / SOURCE_SCHEMA_PATH)
    yaml_content = build_yaml_projection(root)
    if load_yaml_model(yaml_content) != source:
        raise ProjectionError("YAML projection and JSON source values differ")
    validate_graphql_projection(root)
    validate_coverage_ledger(root)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        choices=("check", "print-ledger", "print-yaml"),
        default="check",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "print-ledger":
            sys.stdout.buffer.write(render_coverage_ledger(args.root))
        elif args.command == "print-yaml":
            sys.stdout.buffer.write(build_yaml_projection(args.root))
        else:
            validate_projections(args.root)
            count = len(extract_constraint_tuples(args.root))
            print(
                "Schema projection validation passed: YAML semantic equality, "
                f"GraphQL composition, and {count} exact constraint tuples."
            )
    except (OSError, ProjectionError) as exc:
        print(f"Schema projection validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
