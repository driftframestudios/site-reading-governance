# Site Reading Governance

This repository provides the shared schemas, examples, release evidence,
language rules, and governance guidance used by the five-repository LIMS/ELN
suite. Planning, implementation, simulation, and comparison repositories use
its versioned contracts for decisions, scenarios, receipts, acceptance,
comparison, and change-triggered review.

Repository authorship and maintenance provenance is recorded in
[`AUTHORS`](AUTHORS). Git history and reviewed pull requests preserve change
chronology and contribution credit.

## Start here

1. Read [`GOVERNANCE.md`](GOVERNANCE.md) for meaning, decision rights, evidence
   stages, review, and recovery.
2. Use [`schemas/README.md`](schemas/README.md) to find the record you need, then
   keep its stable identifier and release coordinate with each validation.
3. Run `make check` with Python 3.11 or newer. Use the focused validation
   command in [Quick start](#quick-start) when checking one downstream record.
4. Start changes from `develop` using [`BRANCHING.md`](BRANCHING.md). Read
   [`promotion-receipt.json`](promotion-receipt.json) when the accepted tag,
   commit, archive digest, or release state affects the work.
5. Use the repository-local
   [`governance-schema-release-lineage`](.agents/skills/governance-schema-release-lineage/SKILL.md)
   skill when one schema needs to be followed from source through release and
   its byte-identical Pages retrieval copy.

[`first-receipt.json`](first-receipt.json) provides compact re-entry context.
[`coordination-horizon.json`](coordination-horizon.json) records current work
and the next evidence-bearing move.

The package is private-repository ready. Its examples use synthetic identifiers,
its automation uses read-only permissions by default, and its ruleset exports
can be reviewed before installation through the GitHub Rulesets API.

The current governance schema candidate is `2.0.1`; stable schema identifiers use
the `/v2.0/` coordinate. It implements **Control Plane Profile v0.3**, the
Enterprise Human-AI Practitioner Registry-derived capability profile for
bounded callers, veracity, orientation, coordination, and future-reality
simulation.

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

Every evidence-bearing document records independent mode and assurance
dimensions:

- `evidence_mode`: `planned`, `simulated`, or `observed`
- `assurance_stage`: `specified`, `verified`, `qualified`, `validated`, or
  `accepted`

A standard assurance receipt can model a projected accepted state while
retaining `evidence_mode: simulated`, `authority: simulation_only`, and
`actual_acceptance_required: true`.

The v0.3 simulated-closure contract supplies a second, explicit posture for a
selected future reality:

- `closure_status: closed_in_simulation`
- `environment_observed_closure: separate_unasserted_state`
- `production_authorization_effect: none`

This posture lets an executable simulation fully close the four substantive
receipt families through modeled roles and synthetic environments. It makes no
claim about a separately observed environment or production authorization.

## Database change assurance

Six additive contracts make database evolution inspectable from discovery to
release:

```text
data contract
  -> refactor finding
  -> migration plan
  -> migration receipt
  -> data reconciliation
  -> database release manifest
```

The chain preserves logical meaning alongside physical representation. A plan
records source and target schema digests, immutable script and tool coordinates,
ordered expand/backfill/validate/cutover/contract phases, lock and statement
budgets, compatibility, approval, and recovery. Execution receipts and exact
reconciliation bind observed or simulated results back to that plan. The release
manifest assembles migration, restore, acceptance, finding, and evidence-bundle
coordinates into one reviewable promotion surface.

The contracts remain migration-tool neutral. The current synthetic exemplar
selects Flyway Community 13.0.0 for repository-owned PostgreSQL schema evolution.
Flyway owns ordering, checksums, schema history, deployment serialization, and
per-migration transaction handling. Reviewed SQL and acceptance evidence own
domain constraints, upgrade preconditions, scientific reconciliation, security,
restore rehearsal, and release disposition. Vendor-owned LIMS and ELN databases
continue through vendor-supported lifecycle paths, while cross-platform data
movement produces separate checkpoint and reconciliation receipts.

Native database types preserve instants, civil dates, exact measurements,
booleans, identifiers, and relational integrity. Interchange documents render
migration instants as RFC 3339 UTC values while the data contract retains the
database-native representation.

## Quick start

Requirements: Python 3.11 or newer. The validation path uses the Python standard
library and carries zero runtime package dependencies.

```bash
python3 tools/validate_governance.py
python3 tools/check_language.py
python3 tools/check_language.py --format sarif
python3 tools/scan_secret_shapes.py
python3 -m unittest discover -s tests -v
```

The standard-library Governance Pages builder prepares a deterministic,
reviewable retrieval artifact after a release receiver supplies a structured
proof for the exact accepted source revision. See
[`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) for the clean-source,
two-build, manifest, and optional canonical-origin paths.

After a later receipt records an accepted release subject, verify its annotated
tag, commit, reproducible archive digest, ancestry, and carrier bytes from Git:

```bash
python3 tools/validate_governance.py --verify-release-coordinate
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
  affirmative semantic-field guidance and authoritative language policy
- [`language-policy/`](language-policy/) — digest-pinned policy manifest,
  89-case union corpus, and exact reviewed exemption inventory
- [`docs/AUTHOR_FEEDBACK.md`](docs/AUTHOR_FEEDBACK.md) — advisory,
  structure-aware Vale scope, rule severity, and checksum-verified tool
  coordinate
- [`docs/SEMANTIC_SHADOW_REVIEW.md`](docs/SEMANTIC_SHADOW_REVIEW.md) —
  inactive, bounded contract for qualifying future semantic author feedback
- [`docs/CONTROL_PLANE_V0_3.md`](docs/CONTROL_PLANE_V0_3.md) — bounded caller,
  Practitioner Probe, Coordination Horizon, Machine Node, veracity, and
  simulated-closure operating model
- [`docs/MIGRATION_V1_TO_V2.md`](docs/MIGRATION_V1_TO_V2.md) — downstream
  migration sequence and release validation
- [`docs/MIGRATION_V2_0_0_TO_V2_0_1.md`](docs/MIGRATION_V2_0_0_TO_V2_0_1.md) —
  patch migration for promotion receipts, immutable workflow inputs, and policy
  contexts
- [`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) — deterministic
  Governance 2.0.1 schema retrieval, source proof, authority, and publication
  handoff
- [`schemas/`](schemas/) — JSON Schema 2020-12 contracts
- [`examples/`](examples/) — valid synthetic exemplars for every contract
- [`machine-node.json`](machine-node.json), [`first-receipt.json`](first-receipt.json),
  [`coordination-horizon.json`](coordination-horizon.json), and
  [`promotion-receipt.json`](promotion-receipt.json) — root orientation and
  executable promotion records
- [`.github/workflows/`](.github/workflows/) — reusable validation workflows
- [`rulesets/`](rulesets/) — reviewable GitHub repository ruleset exports
- [`audits/repository-security-review-2026-07-28.md`](audits/repository-security-review-2026-07-28.md)
  — five-repository review scope, remediations, evidence boundaries, and open
  production receipts
- [`audits/dependency-automation-review-2026-07-28.md`](audits/dependency-automation-review-2026-07-28.md)
  — five-repository bot-identity, branch grammar, workflow, and follow-up review
- [`tools/`](tools/) and [`tests/`](tests/) — dependency-free contract,
  repository-independent language core with a bounded governance wrapper,
  secret-shape checks, and regression validation

## Versioning

Schema releases follow semantic versioning:

- major: downstream documents require an intentional migration;
- minor: backward-compatible contract capability;
- patch: clarification, example, or validation repair.

Consumers pin the annotated release tag, its accepted commit, and the SHA-256
digest of `git archive --format=tar <commit>`. Floating branch references
support local exploration; governed comparisons use immutable release
coordinates.

## Source posture

[`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md) is the
public authority for this repository's applied language posture. It records the
desired-state guidance, hard-boundary treatment, automated checks, and exact
local verification path. Working-source lineage remains with its authorized
steward while this repository-local guide gives public collaborators the
complete behavior needed here.
