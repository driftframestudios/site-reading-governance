# Governance

## Purpose

Site Reading governance makes comparative work inspectable. Each decision,
forecast, implementation result, receipt, and acceptance can be located,
reproduced, challenged, superseded, and traced to accountable authority.

## Governing principles

1. **Authority is explicit.** Desired behavior, running-system truth, simulated
   behavior, comparison records, and organizational acceptance remain distinct.
2. **Evidence context is explicit.** A receipt identifies its mode, environment,
   build, configuration, fixture, test, performer or modeled role, reviewer,
   assumptions, and limitations.
3. **Forecasts remain recoverable.** Published simulation baselines are
   immutable. Learning creates a new release and preserves the earlier forecast.
4. **Comparison is symmetric.** A divergence can reveal an implementation gap,
   a simulation fault, a shared specification violation, or a context change.
5. **Acceptance is plural.** Scientific, Quality, Regulatory, security,
   operations, and business authorities make their own decisions.
6. **Change activates re-evaluation.** Source, dependency, schema, fixture,
   configuration, environment, intended-use, and owner changes create
   invalidation records for affected claims.
7. **Desired states lead.** Governance text, automation, comments, and
   identifiers describe the target behavior directly.
8. **Callers receive bounded authority.** Services own named operations and
   enforce typed input, scope, effect class, budget, approval, idempotency,
   audit, and recovery at the execution boundary.
9. **Orientation informs.** Machine Nodes and first receipts describe current
   state and handoff while released policy and runtime identity authorize
   effects.

## Decision rights

| Decision | Recommends | Reviews | Accountable authority |
| --- | --- | --- | --- |
| Specification meaning | Product and domain engineering | Scientific and platform representatives | Program owner |
| Scientific suitability | Scientific leads | Data and laboratory operations | Scientific authority |
| Quality suitability | Validation and Quality engineering | Process owners | Quality authority |
| Regulatory applicability | Regulatory specialist | Legal and Quality | Regulatory authority |
| Security and privacy posture | Security and privacy engineering | Platform operations | Security/privacy authority |
| Production operation | Platform and service owners | Support and laboratory operations | Operational authority |
| Simulation forecast | Simulation maintainers | Domain and implementation peers | Simulation steward |
| Divergence classification | Evidence maintainers | Affected domain owners | Comparison steward |

Repository approval demonstrates engineering governance. Acceptance records
demonstrate the separate organizational decision named by their `acceptance_type`.

## Evidence lifecycle

```text
specified -> verified -> qualified -> validated -> accepted
```

- **Specified:** behavior and success criteria are versioned.
- **Verified:** local or controlled execution supports the claim.
- **Qualified:** the named environment and configuration support the claim.
- **Validated:** accountable evidence supports fitness for intended use.
- **Accepted:** a named authority authorizes the stated scope.

Each transition produces a receipt or acceptance record. Higher stages reference
the evidence that supports the transition. A future-reality simulation can model
the complete lifecycle through `accepted` while retaining simulated evidence and
simulation-only authority.

## Substantive receipt families

The delivery constellation tracks these families as first-class gates:

1. configured Sapio, Benchling, and LabKey environments;
2. representative migration, cutover, rollback, restore, continuity, and data
   exit rehearsals;
3. production security, privacy, observability, support, and incident exercises;
4. separate accountable scientific, Quality, and Regulatory acceptance.

Control Plane Profile v0.3 supports two distinct closure states:

- **simulated closure** selects a versioned future reality, executes synthetic
  scenarios, binds artifacts and assumptions, and closes all four families
  inside that simulation;
- **environment-observed closure** records separately observed system and
  organizational evidence when a later collaboration elects to pursue it.

A simulated closure uses modeled authority roles, requires no named person, and
creates no production authorization. The closure manifest keeps these
properties machine-verifiable.

## Bounded caller lifecycle

```text
caller contract
  -> service-owned operation
  -> boundary decision
  -> scoped approval when required
  -> effect
  -> call receipt
  -> owned recovery or replay
```

The service boundary establishes identity, validates typed input, constrains
tenant and record scope, applies the caller authority ceiling, enforces resource
budgets, and records each decision. Broad and irreversible effects carry scoped,
expiring approval. Side effects carry durable idempotency fingerprints.

## Coordination Horizon

A Coordination Horizon expresses sequenced work without prescribing a fixed
number of temporal buckets. It records current items, entry and completion
evidence, dependencies, retained effects, consequential questions, and a
re-entry capsule. Teams can choose labels and cadence that fit the work.

## Governed dependency automation

Dependency automation follows a bounded-caller posture. An exception to the
human GitFlow branch families requires three facts together: a complete
Dependabot or Renovate branch grammar, the exact corresponding pull-request
author, and a `main` or `develop` target. Ordinary tests, immutable action
references, CODEOWNER review, and release evidence continue to apply.

The enabled package ecosystem and admitted branch grammar advance in the same
reviewed change. Dependabot-triggered workflows use read-only repository
permission and Dependabot-scoped secrets. Security updates may still target the
default `main` branch, and an accepted repair is reconciled into `develop`.
The branch-admission gate uses a dedicated, read-only `pull_request_target`
workflow to read pull-request coordinates while executing the checker from the
exact base commit in `.branch-policy-base`. Proposed head content enters the
ordinary `pull_request` validation path and supplies only quoted branch and
author coordinates to the base-controlled policy.

The branch-policy workflow and checker become active after their reviewed
versions exist on the default branch and each protected target branch. The
introducing pull request continues under the previously released controls, and
the accepted policy is merged forward before it governs later proposals.

The behavioral basis is maintained in GitHub's
[Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
and
[Dependabot on GitHub Actions](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-on-actions).

## Database change lifecycle

```text
primitive inventory
  -> approved data contract
  -> located refactor findings
  -> expand and backfill
  -> reconcile and validate
  -> cut over through a compatibility window
  -> accountable contract-phase approval
  -> release manifest
```

The data contract defines semantic and physical types, units, precision,
temporal meaning, keys, constraints, classification, retention, and compatible
application releases. A refactor finding records the current primitive, its
material effect, the affirmative target, evidence, ownership, recovery route,
and migration disposition.

Migration plans bind immutable tool and script coordinates to source and target
schema digests. Each phase carries transaction posture, online behavior, lock
and statement budgets, durable checkpoints, preconditions, and observable
success criteria. Destructive contract phases enter through a measured
compatibility window and scoped approval. The migration runner uses one reviewed
writer coordinate and records schema-drift and applied-checksum verification.

Execution receipts preserve phase outcomes, operational measurements,
reconciliation, backup or recovery-point coordinates, restore evidence, and
accountable review. Reconciliation binds its exact values and scientific
invariants to a named cohort and query digest. The database release manifest
assembles the contract, migration graph, supported baselines, receipts,
acceptance decisions, findings, and immutable evidence bundle.

## Change and invalidation

An invalidation record states:

- the triggering change;
- affected specifications, decisions, scenarios, receipts, and acceptances;
- the earlier assurance state;
- the replacement evaluation;
- accountable owner and target date;
- resolution and successor evidence.

The repository preserves superseded records. Current indexes point to active
successors while retaining the complete lineage.

## Comparative review

Comparison releases pin:

- specification release and digest;
- simulation release and digest;
- implementation commit and digest;
- fixture bundle and digest;
- comparator commit and receipt-schema version.

Material differences use the shared classification catalog:
`converged`, `desired_divergence`, `actual_gap`, `actual_defect`,
`simulation_fault`, `shared_specification_violation`, `context_changed`,
`receipt_pending`, or `comparison_inconclusive`.

Critical scientific, security, audit, signature, and recovery invariants require
exact agreement. Performance and operational characteristics use approved
tolerances with numerator, denominator, threshold, window, and observed value.

## Review cadence

- Pull request: schema, language, example, and policy validation.
- Weekly: assumption aging and open divergence review.
- Monthly: substantive receipt ledger review.
- Release: cross-role governance approval and digest publication.
- Material change: affected-evidence analysis and invalidation record.

## Hard safety and privacy boundary

Raw credentials, regulated records, personal data, exploitable security findings,
and unredacted tenant evidence stay in approved governed stores; repository
records contain synthetic examples or redacted, digest-bound locators.

**PRIVACY BOUNDARY:** these materials must not enter Git history; the replacement behavior is storage in the approved evidence system with least-privilege access, retention, and audit, and the repository content scan verifies that committed examples contain synthetic data or redacted locators.
