# Status

## Maintained

| Surface | Verification |
| --- | --- |
| Data-contract schema and example | JSON Schema 2020-12 plus focused semantic tests |
| Database primitive ledger | JSON Schema 2020-12 plus direct target-state checks |
| Practitioner Probe structure | JSON Schema 2020-12 |
| Machine Node and Coordination Horizon | Independent JSON Schema validation |
| Editorial guidance | Vale with repository-owned styles |
| Repository hygiene | GitHub secret scanning, push protection, and native repository controls |

## Historical reference

Approval, acceptance, bounded-caller, call-receipt, simulated closure, database
release receipt, and promotion models remain available as design history. The
active validator excludes these records.

## Current focus

The immediate work is deliberately small:

1. keep the LIMS/ELN data primitive contract internally coherent;
2. keep the refactor ledger precise and direct;
3. keep Machine Nodes useful as hydration material; and
4. use established tools for migration, repository policy, and schema validation.
