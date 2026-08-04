# Schema Catalog

All contracts use JSON Schema 2020-12 and stable HTTPS identifiers.
Release candidate `2.0.1` uses the stable `/v2.0/` identifier coordinate and implements
Control Plane Profile v0.3.

| Schema | Record |
| --- | --- |
| `constellation.schema.json` | Repository topology, authority, and release policy |
| `specification.schema.json` | Desired behavior, rules, scenarios, and acceptance roles |
| `scenario.schema.json` | Given/When/Then example with material effect and recovery |
| `decision.schema.json` | Selected option, alternatives, named probability event, horizon, basis, conditions, and falsifiers |
| `coordination-horizon.schema.json` | Flexible work horizon, completion evidence, retained effects, and re-entry |
| `bounded-caller.schema.json` | Caller identity, authority ceiling, scope, tools, egress, budget, audit, and recovery |
| `operation.schema.json` | Service-owned typed operation, effect class, approval, idempotency, and verification |
| `approval.schema.json` | Scoped, expiring organizational or future-reality operation decision |
| `effect.schema.json` | Attributable state effect, evidence mode, digests, and recovery |
| `call-receipt.schema.json` | Caller, operation, boundary decision, approval, effect, result, and resource audit |
| `claim-veracity.schema.json` | Claim status, source band, verification, limitations, and recheck triggers |
| `practitioner-probe.schema.json` | Five-level probe, technical core, review surfaces, scenarios, and instruction yield |
| `machine-node.schema.json` | Non-authorizing machine orientation, provenance, campaigns, contracts, and consumers |
| `first-receipt.schema.json` | Compact entry orientation, evidence posture, source permissions, and handoff |
| `promotion-receipt.schema.json` | Candidate and observed repository-promotion evidence |
| `simulated-receipt-closure.schema.json` | Executable future-reality closure of all four substantive receipt families |
| `simulation-assumption.schema.json` | Time-bounded assumption, basis, owner, and falsifiers |
| `receipt.schema.json` | Environment-bound assurance evidence |
| `acceptance.schema.json` | Scientific, Quality, Regulatory, and other accountable decisions |
| `comparison.schema.json` | Pinned actual/simulation result and adjudication |
| `invalidation.schema.json` | Change-triggered re-evaluation and successor evidence |
| `language-control.schema.json` | Typed target, boundary, replacement, verification, ownership, and evidence for high-consequence instructions |
| `data-contract.schema.json` | Logical and physical database meaning, constraints, compatibility, and invalidation triggers |
| `database-refactor-finding.schema.json` | Located primitive finding, material effect, target state, disposition, ownership, and migration linkage |
| `database-migration-plan.schema.json` | Ordered expand-through-contract phases, execution budgets, compatibility window, approval, and recovery |
| `database-migration-receipt.schema.json` | Plan-bound execution, phase outcomes, environment coordinate, measurements, and recovery evidence |
| `data-reconciliation.schema.json` | Cohort-bound exact comparisons, scientific invariants, exceptions, and accountable review |
| `database-release-manifest.schema.json` | Contract, ordered migration, receipt, acceptance, finding, and evidence-bundle release coordinate |
| `common.schema.json` | Shared identifiers, actors, artifacts, metrics, and boundaries |

## Contract invariants

- Simulated receipts use simulation authority and retain actual acceptance as an
  explicit future gate.
- Accepted receipts use observed evidence, organizational authority, and a named
  accountable approver.
- Simulated acceptance records remain projections.
- Actual accountable acceptance uses observed evidence.
- A future-reality manifest can close all four substantive families inside the
  simulation while environment-observed closure remains a separate, unasserted
  evidence state.
- Broad and irreversible operations require scoped approval before an
  authorized call can carry effects.
- Machine Nodes and first receipts remain orientation-only.
- Practitioner Probes carry the complete one-through-five proficiency ladder.
- Probabilities name their event, horizon, basis, conditions, recalibration
  triggers, and falsifiers.
- Governance records close their property surface to make drift visible.
- Hard safety, privacy, and Regulatory boundaries include protected state,
  explicit constraint, replacement behavior, and verification.
- Consequential language controls bind an affirmative target and safe replacement
  to an accountable owner, observable verification, and durable evidence.
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

## Consumer pinning

Downstream repositories pin the governance release, commit, and digest. The
reusable contract workflow validates each document with the selected schema from
that immutable coordinate.

Artifact locators use opaque `governed://` or `evidence://` references. Date-time
values carry an RFC 3339 timezone, migration evidence serializes instants in
canonical UTC, and numeric values remain finite. Database contracts express
native temporal and exact-numeric storage separately from interchange encoding.

## Evolution

Compatible fields arrive in minor releases. Consumer-shaping changes arrive in
major releases with examples, migration guidance, and invalidation analysis.
