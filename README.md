# Site Reading Governance

This repository is a compact documentation library for the Site Reading
constellation. Its maintained surface helps collaborators understand data
contracts, database primitive findings, Practitioner Probes, current work, and
the location of related repositories.

Application permissions live in application identity and policy systems.
Scientific, Quality, Regulatory, security, operational, and production
decisions live in their established systems of record. This repository supplies
documentation and examples for technical collaboration.

## Maintained surface

| Artifact | Purpose |
| --- | --- |
| `schemas/data-contract.schema.json` | Semantic and physical database contract |
| `examples/data-contract.json` | Synthetic LIMS/ELN contract example |
| `schemas/database-refactor-finding.schema.json` | Direct primitive-change ledger entry |
| `examples/database-refactor-finding.json` | Timestamp primitive correction example |
| `schemas/practitioner-probe.schema.json` | Principal-level probe structure |
| `machine-node.json` | Durable collaboration orientation |
| `coordination-horizon.json` | Current work and re-entry context |

The remaining control-plane, approval, acceptance, receipt, closure, and release
records are historical design material. They stay available for provenance and
remain outside the active validator. See
[`reference/HISTORICAL_MODELS.md`](reference/HISTORICAL_MODELS.md).

## Established tools

The repository delegates common platform concerns to maintained tools:

| Concern | Tool or pattern |
| --- | --- |
| JSON Schema 2020-12 | Python `jsonschema` |
| Repository branch policy | GitHub Rulesets and protected branches |
| Dependency updates | Dependabot |
| Editorial feedback | Vale |
| PostgreSQL migration execution | Flyway |
| Transactional event publication | Thin outbox with Debezium or the selected CDC platform |

Repository code adds only the small amount of mapping required to validate the
maintained examples. It supplies no migration runner, broker, workflow product,
policy engine, approval service, or acceptance system.

## Data-contract focus

The synthetic contract demonstrates the material target state:

- PostgreSQL `timestamptz` for instants and `date` for civil dates;
- `numeric` profiles for exact scientific quantities;
- `uuid` for internal identity and bounded text for external identifiers;
- tenant-leading composite keys and forced row-level security;
- controlled vocabularies and UCUM unit mappings;
- result qualifiers, reference intervals, detection and quantitation limits;
- conversion formula and factor provenance;
- binary SHA-256 digests for semantic envelopes and source artifacts; and
- append-only result events with explicit supersession.

Flyway owns migration discovery, ordering, checksums, schema history, locking,
and execution. The application uses expand-and-contract changes where releases
need a compatibility window. Vendor-owned LIMS and ELN databases use their
vendor-supported lifecycle paths.

Cross-service delivery uses a thin transactional outbox. The source transaction
stores the domain change and minimal event envelope; Debezium or the selected CDC
platform publishes it; consumers implement idempotency and observable outcomes.

## Local validation

Requirements: Python 3.11 or newer.

```bash
python3 -m pip install --requirement requirements-dev.txt
python3 tools/validate_governance.py
vale --config=.vale.ini --no-global --minAlertLevel=warning .
python3 -m unittest discover -s tests -v
```

Validate one document explicitly:

```bash
python3 tools/validate_governance.py \
  --schema schemas/data-contract.schema.json \
  --document examples/data-contract.json
```

## Repository map

- [`GOVERNANCE.md`](GOVERNANCE.md) — maintained scope and design guardrails
- [`schemas/`](schemas/) and [`examples/`](examples/) — documentary contracts
- [`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md) —
  affirmative instruction guidance
- [`machine-node.json`](machine-node.json) — collaboration hydration
- [`coordination-horizon.json`](coordination-horizon.json) — current work context
- [`rulesets/`](rulesets/) — reviewable GitHub Ruleset exports
- [`.github/workflows/`](.github/workflows/) — focused validation automation

Schema releases follow semantic versioning. Downstream repositories pin a
reviewed release when they adopt a maintained contract.
