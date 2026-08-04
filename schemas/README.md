# Schema Catalog

All schemas use JSON Schema 2020-12 and stable HTTPS identifiers.

## Maintained contracts

| Schema | Documentary purpose |
| --- | --- |
| `data-contract.schema.json` | Logical and physical database meaning |
| `database-refactor-finding.schema.json` | Located primitive finding and direct target state |
| `practitioner-probe.schema.json` | Principal-level probe structure |
| `machine-node.schema.json` | Collaboration hydration |
| `coordination-horizon.schema.json` | Current work and re-entry context |
| `common.schema.json` | Shared identifiers and metadata |

The active example mapping lives in `tools/validate_governance.py`. Validation
delegates JSON Schema evaluation to the maintained Python `jsonschema` package.

## Historical contracts

Earlier explorations of specifications, decisions, bounded callers, approvals,
effects, receipts, acceptance, comparison, simulated closure, and database
release evidence live under `reference/quarantine/`. They remain available for
provenance and stay outside the maintained release surface.

## Evolution

Compatible additions use a minor schema release. Consumer-shaping changes use a
major release with an updated example and migration note. Corrections use a
patch release.
