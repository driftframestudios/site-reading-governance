# Schema catalog

## Purpose

This catalog helps a collaborator choose the JSON Schema that owns a
Governance record shape and open that contract directly.

## Authority

The linked files use JSON Schema 2020-12 and define the machine-checkable
structure for the selected repository revision. Governance 2.2.0 retains the
stable `/v2.0/` identifier family. [`../GOVERNANCE.md`](../GOVERNANCE.md)
defines meaning and decision rights; schemas define structure; accountable
roles retain material suitability and acceptance.

The YAML and GraphQL promotion-receipt forms remain candidate retrieval
projections. [`promotion-receipt.schema.json`](promotion-receipt.schema.json)
continues to be their validation authority.

## Use

Choose the record whose description matches the decision or evidence you need,
then keep its stable `$id` and accepted release coordinate with each governed
validation.

| Schema | Record |
| --- | --- |
| [`constellation.schema.json`](constellation.schema.json) | Repository topology, authority, and release policy |
| [`specification.schema.json`](specification.schema.json) | Desired behavior, rules, scenarios, and acceptance roles |
| [`scenario.schema.json`](scenario.schema.json) | Given/When/Then example with material effect and recovery |
| [`decision.schema.json`](decision.schema.json) | Selected option, alternatives, named probability event, horizon, basis, conditions, and falsifiers |
| [`coordination-horizon.schema.json`](coordination-horizon.schema.json) | Flexible work horizon, completion evidence, retained effects, and re-entry |
| [`bounded-caller.schema.json`](bounded-caller.schema.json) | Caller identity, authority ceiling, scope, tools, egress, budget, audit, and recovery |
| [`operation.schema.json`](operation.schema.json) | Service-owned typed operation, effect class, approval, idempotency, and verification |
| [`approval.schema.json`](approval.schema.json) | Scoped, expiring organizational or future-reality operation decision |
| [`effect.schema.json`](effect.schema.json) | Attributable state effect, evidence mode, digests, and recovery |
| [`call-receipt.schema.json`](call-receipt.schema.json) | Caller, operation, boundary decision, approval, effect, result, and resource audit |
| [`claim-veracity.schema.json`](claim-veracity.schema.json) | Claim status, source band, verification, limitations, and recheck triggers |
| [`practitioner-probe.schema.json`](practitioner-probe.schema.json) | Five-level probe, technical core, review surfaces, scenarios, and instruction yield |
| [`machine-node.schema.json`](machine-node.schema.json) | Non-authorizing machine orientation, provenance, campaigns, contracts, and consumers |
| [`first-receipt.schema.json`](first-receipt.schema.json) | Compact entry orientation, evidence posture, source permissions, and handoff |
| [`promotion-receipt.schema.json`](promotion-receipt.schema.json) | Candidate readiness and a later observation of the accepted tagged release subject |
| [`simulated-receipt-closure.schema.json`](simulated-receipt-closure.schema.json) | Executable future-reality closure of all four substantive receipt families |
| [`simulation-assumption.schema.json`](simulation-assumption.schema.json) | Time-bounded assumption, basis, owner, and falsifiers |
| [`receipt.schema.json`](receipt.schema.json) | Environment-bound assurance evidence |
| [`acceptance.schema.json`](acceptance.schema.json) | Scientific, Quality, Regulatory, and other accountable decisions |
| [`comparison.schema.json`](comparison.schema.json) | Pinned actual/simulation result and adjudication |
| [`invalidation.schema.json`](invalidation.schema.json) | Change-triggered re-evaluation and successor evidence |
| [`language-control.schema.json`](language-control.schema.json) | Typed target, boundary, replacement, verification, ownership, and evidence for high-consequence instructions |
| [`data-contract.schema.json`](data-contract.schema.json) | Logical and physical database meaning, constraints, compatibility, and invalidation triggers |
| [`database-refactor-finding.schema.json`](database-refactor-finding.schema.json) | Located primitive finding, material effect, target state, disposition, ownership, and migration linkage |
| [`database-migration-plan.schema.json`](database-migration-plan.schema.json) | Ordered expand-through-contract phases, execution budgets, compatibility window, approval, and recovery |
| [`database-migration-receipt.schema.json`](database-migration-receipt.schema.json) | Plan-bound execution, phase outcomes, environment coordinate, measurements, and recovery evidence |
| [`data-reconciliation.schema.json`](data-reconciliation.schema.json) | Cohort-bound exact comparisons, scientific invariants, exceptions, and accountable review |
| [`database-release-manifest.schema.json`](database-release-manifest.schema.json) | Contract, ordered migration, receipt, acceptance, finding, and evidence-bundle release coordinate |
| [`administrative-assurance.schema.json`](administrative-assurance.schema.json) | Candidate profile 0.1: source-bound evidence, population accounting, scoped review, and successor recovery |
| [`common.schema.json`](common.schema.json) | Shared identifiers, actors, artifacts, metrics, and boundaries |

[`../examples/example-map.json`](../examples/example-map.json) owns the mapping
from each standalone record schema to its synthetic example. `common.schema.json`
supplies shared definitions and therefore has no standalone example.

### Contract invariants

- Simulated receipts use simulation authority and retain actual acceptance as
  an explicit future gate.
- Accepted receipts use observed evidence, organizational authority, and a
  named accountable approver.
- A future-reality manifest can close all four substantive families inside the
  simulation while environment-observed closure remains a separate evidence
  state.
- Broad and irreversible operations require scoped approval before an
  authorized call can carry effects.
- Machine Nodes and first receipts remain orientation-only.
- Practitioner Probes carry the complete one-through-five proficiency ladder.
- Probabilities name their event, horizon, basis, conditions, recalibration
  triggers, and falsifiers.
- Governance records close their property surface so drift remains visible.
- Hard safety, privacy, and Regulatory boundaries include protected state,
  explicit constraint, replacement behavior, and verification.
- Consequential language controls bind an affirmative target and safe
  replacement to an accountable owner, observable verification, and durable
  evidence.
- Data contracts preserve semantic type, physical type, nullability, units,
  precision, temporal meaning, keys, constraints, retention, and compatibility.
- Migration plans sequence bounded phases, retain immutable applied checksums,
  and establish approval and recovery before a destructive contract phase.
- Migration receipts bind the exact plan, tool, script, environment, source
  schema, target schema, phase results, reconciliation, and restore evidence.
- Reconciliation records keep counts and measured values exact, bind the cohort
  and query digest, and record accountable dispositions for exceptions.
- Database release manifests bind one contract and evidence chain while keeping
  simulated authority distinct from environment-observed promotion.
- Release observations distinguish the accepted annotated tag and source commit
  from the later receipt carrier, then bind exact Git tar archive bytes with
  SHA-256.

### Consumer pinning

Downstream repositories pin the Governance release tag, accepted commit, and
archive digest. The reusable contract workflow validates each document with
the selected schema from that immutable coordinate.

Artifact locators use opaque `governed://` or `evidence://` references.
Date-time values carry an RFC 3339 timezone, migration evidence serializes
instants in canonical UTC, and numeric values remain finite. Database contracts
express native temporal and exact-numeric storage separately from interchange
encoding.

## Verify

From the repository root, run the focused catalog and example checks:

```bash
python3 tools/validate_governance.py
python3 -m unittest \
  tests.test_governance.GovernancePackageTests.test_schema_catalog_is_coherent \
  tests.test_governance.GovernancePackageTests.test_every_mapped_example_validates \
  -v
```

These checks establish catalog membership, stable schema identifiers, example
mapping, and declared structural invariants. Domain fitness and accountable
acceptance remain with the receiving review.

## Next route

- Use [`../schema-projections/README.md`](../schema-projections/README.md) for
  the bounded YAML and GraphQL pilot.
- Use [`../docs/ADOPTION.md`](../docs/ADOPTION.md) for downstream pinning and
  validation.
- Use
  [`governance-schema-release-lineage`](../.agents/skills/governance-schema-release-lineage/SKILL.md)
  when one schema needs to be traced through release and public retrieval.
- Use [`../GOVERNANCE.md`](../GOVERNANCE.md) when meaning, authority, or
  acceptance changes the decision.

Compatible fields arrive in minor releases. Consumer-shaping changes arrive in
major releases with examples, migration guidance, and invalidation analysis.

## Return to repository root

[Return to the repository orientation](../README.md).
