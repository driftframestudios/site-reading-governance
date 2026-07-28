# Site Reading Governance

This repository is the reusable governance plane for comparative Site Reading
constellations. It gives planning, implementation, simulation, and evidence
repositories one versioned contract for decisions, scenarios, receipts,
acceptance, comparison, and change-triggered invalidation.

The package is private-repository ready. Its examples use synthetic identifiers,
its automation uses read-only permissions by default, and its ruleset exports
can be reviewed before installation through the GitHub Rulesets API.

## Constellation

| Repository role | Purpose | Authority |
| --- | --- | --- |
| Program specification | Intent, examples, risks, forecasts, and acceptance criteria | Desired behavior |
| Enterprise implementation | Current code, infrastructure, migrations, and runbooks | Running implementation |
| Simulated final state | Executable counterfactual with explicit assumptions | Forecast behavior |
| Comparative evidence | Fixtures, normalizers, paired runs, and divergence adjudication | Comparison record |
| Site Reading governance | Shared schemas, workflows, templates, and policy exports | Governance contract |

Runtime code flows from the program specification into each implementation
through released, digest-pinned contracts. Learning flows back through reviewed
decision records. The actual implementation and simulated final state maintain
independent source histories.

## Assurance grammar

Every evidence-bearing document records two independent dimensions:

- `evidence_mode`: `planned`, `simulated`, or `observed`
- `assurance_stage`: `specified`, `verified`, `qualified`, `validated`, or
  `accepted`

A simulation can model a projected accepted state while retaining
`evidence_mode: simulated`, `authority: simulation_only`, and
`actual_acceptance_required: true`. Accountable scientific, Quality, and
Regulatory decisions use observed evidence and named organizational authority.

## Quick start

Requirements: Python 3.11 or newer. The validation path uses the Python standard
library and carries zero runtime package dependencies.

```bash
python3 tools/validate_governance.py
python3 tools/check_language.py
python3 -m unittest discover -s tests -v
```

Validate a downstream document against this package:

```bash
python3 tools/validate_governance.py \
  --schema schemas/receipt.schema.json \
  --document path/to/receipt.json
```

## Contents

- [`GOVERNANCE.md`](GOVERNANCE.md) — authority, decision, evidence, and review
  model
- [`BRANCHING.md`](BRANCHING.md) — GitFlow-like lifecycle and release protocol
- [`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md) —
  affirmative semantic-field guidance
- [`schemas/`](schemas/) — JSON Schema 2020-12 contracts
- [`examples/`](examples/) — valid synthetic exemplars for every contract
- [`.github/workflows/`](.github/workflows/) — reusable validation workflows
- [`rulesets/`](rulesets/) — reviewable GitHub repository ruleset exports
- [`tools/`](tools/) and [`tests/`](tests/) — dependency-free validation

## Versioning

Schema releases follow semantic versioning:

- major: downstream documents require an intentional migration;
- minor: backward-compatible contract capability;
- patch: clarification, example, or validation repair.

Consumers pin a release tag and digest. Floating branch references support local
exploration; governed comparisons use immutable release coordinates.

## Source posture

The language policy is derived from the Notion field-guide page
[Semantic Attractor Design — Negation-Aware Instructions](https://app.notion.com/p/abcb29b960a842ce8f1a409408a29257).
The local guide records the applied interpretation and the automated checks.

