# Governance

## Purpose

Site Reading governance makes comparative work inspectable. Each decision,
forecast, implementation result, receipt, and acceptance can be located,
reproduced, challenged, superseded, and traced to accountable authority.

## Governing principles

1. **Authority is explicit.** Desired behavior, running-system truth, simulated
   behavior, comparison records, and organizational acceptance remain distinct.
2. **Evidence is environment-bound.** A receipt identifies its environment,
   build, configuration, fixture, test, performer, reviewer, and limitations.
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
the evidence that supports the transition.

## Required substantive receipt families

The delivery constellation tracks these families as first-class gates:

1. configured Sapio, Benchling, and LabKey environments;
2. representative migration, cutover, rollback, restore, continuity, and data
   exit rehearsals;
3. production security, privacy, observability, support, and incident exercises;
4. separate accountable scientific, Quality, and Regulatory acceptance.

Synthetic and simulated evidence prepares these gates. Observed, environment-bound
evidence closes them.

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

**PRIVACY BOUNDARY:** these materials must not enter Git history; the replacement behavior is storage in the approved evidence system with least-privilege access, retention, and audit.
