# Schema projection pilots

This directory holds reviewed source material for machine-readable forms that
support an accepted JSON Schema. A projection can begin here as a candidate,
receive focused comparison evidence, and reach a later release decision without
changing the authority of the accepted schema family.

## Promotion receipt pilot

`promotion-receipt/v1.0.0/` contains two authored records:

- `promotion-receipt.graphql` describes a bounded GraphQL interface for
  promotion-receipt inspection; and
- `coverage.json` records every constraint reachable from
  `schemas/promotion-receipt.schema.json` and its referenced common definitions.

The JSON Schema remains the executable validation authority. The GraphQL SDL
carries field, type, list, enum, and reusable-type relationships that GraphQL
can express directly. The coverage ledger names the constraints that remain in
JSON Schema, including string grammar, ranges, uniqueness, required-but-nullable
presence, and cross-field conditions.

`tools/schema_projections.py` extracts the complete source constraint set and
requires exact tuple-set equality with the ledger. Each tuple binds its source
document, JSON Pointer, constraint kind, and canonical-value SHA-256 digest.
This makes an added, removed, changed, repeated, or reclassified constraint a
specific review difference rather than a passing count.

The same tool generates the YAML 1.2 semantic twin. It sorts mappings, quotes
every string, uses native JSON scalar forms, emits UTF-8 with LF line endings,
and accepts one document without aliases, anchors, or explicit tags. It parses
the result and compares the canonical data model with the JSON source before
returning any bytes.

## Local proof

Install the two exact parser versions, then run the focused check:

```bash
python3 -m pip install --disable-pip-version-check --require-hashes \
  -r requirements-projections.txt
python3 tools/schema_projections.py
python3 -m unittest tests.test_schema_projections -v
```

The full Governance Pages build publishes the generated YAML, authored SDL,
and coverage ledger at the version-bearing
`schemas/v2.0/projections/promotion-receipt/v1.0.0/` retrieval path. Its
manifest records distinct identifiers for the family and each representation,
marks the family as a candidate, and keeps the JSON validation authority
visible.
