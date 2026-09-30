# Schema projection pilots

## Purpose

This directory holds reviewed machine-readable forms that make an accepted JSON
Schema easier to retrieve or query while preserving one validation authority.

## Authority

[`../schemas/promotion-receipt.schema.json`](../schemas/promotion-receipt.schema.json)
defines the promotion-receipt structure. The generated YAML 1.2 twin and the
authored GraphQL SDL are candidate projections of that source. The exact
coverage ledger records which constraints each representation carries directly
and which remain with JSON Schema.

Projection checks establish structural and semantic agreement with the selected
source bytes. A later release decision owns any standing change.

## Use

`promotion-receipt/v1.0.0/` contains two authored records:

- [`promotion-receipt.graphql`](promotion-receipt/v1.0.0/promotion-receipt.graphql)
  describes a read-only GraphQL interface for promotion-receipt inspection; and
- [`coverage.json`](promotion-receipt/v1.0.0/coverage.json) records every
  constraint reachable from the promotion-receipt schema and its referenced
  common definitions.

The GraphQL SDL carries field, type, list, enum, and reusable-type relationships
that GraphQL can express directly. The ledger identifies string grammar,
ranges, uniqueness, required-but-nullable presence, and cross-field conditions
that stay in JSON Schema.

`tools/schema_projections.py` extracts the complete source constraint set and
requires exact tuple-set equality with the ledger. Each tuple binds its source
document, JSON Pointer, constraint kind, and canonical-value SHA-256 digest.
An added, removed, changed, repeated, or reclassified constraint therefore
appears as a specific review difference.

The same tool generates the YAML 1.2 semantic twin. It sorts mappings, quotes
every string, uses native JSON scalar forms, emits UTF-8 with LF line endings,
and accepts one document without aliases, anchors, or explicit tags. It parses
the result and compares the canonical data model with the JSON source before
returning bytes.

## Verify

From the repository root, install the exact parser versions and run the focused
proof:

```bash
python3 -m pip install --disable-pip-version-check --require-hashes \
  -r requirements-projections.txt
python3 tools/schema_projections.py
python3 -m unittest tests.test_schema_projections -v
```

These checks establish deterministic YAML equality, GraphQL composition and
source binding, and exact constraint-ledger coverage at the inspected revision.
They leave interface promotion and downstream fitness with their release and
consumer reviews.

## Next route

- Return to the accepted structural source in
  [`../schemas/README.md`](../schemas/README.md).
- Follow public artifact construction and identity in
  [`../docs/GOVERNANCE_PAGES.md`](../docs/GOVERNANCE_PAGES.md).
- Follow release standing in
  [`../promotion-receipt.json`](../promotion-receipt.json) and
  [`../STATUS.md`](../STATUS.md).
- Start downstream use with [`../docs/ADOPTION.md`](../docs/ADOPTION.md).

The Governance Pages build publishes the generated YAML, authored SDL, and
coverage ledger at the version-bearing
`schemas/v2.0/projections/promotion-receipt/v1.0.0/` retrieval path. Its
manifest records distinct identifiers for the family and each representation,
marks the family as a candidate, and keeps the JSON validation authority
visible.

## Return to repository root

[Return to the repository orientation](../README.md).
