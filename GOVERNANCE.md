# Governance

## Maintained responsibility

This repository maintains documentary interfaces for data-contract integrity,
database primitive findings, Practitioner Probes, and collaboration hydration.
Each artifact states its technical meaning and material effect in a form that a
human or machine collaborator can inspect.

Operational systems retain their existing responsibilities:

- identity providers and policy engines evaluate application permissions;
- GitHub Rulesets and protected branches enforce repository policy;
- Flyway executes PostgreSQL migrations;
- vendor lifecycle tooling manages vendor-owned databases;
- organizational systems of record capture accountable decisions; and
- observability platforms capture production behavior.

## Design guardrails

1. Add a schema field when it improves implementation meaning or interoperability.
2. Prefer a maintained platform for common enterprise mechanics.
3. Keep examples synthetic and technically plausible.
4. Connect every primitive finding to a concrete target state and migration identifier.
5. Preserve source meaning, scientific units, precision, temporal semantics, and lineage.
6. Keep Machine Nodes concise enough to function as hydration material.
7. Move exploratory control models into historical reference status when they stop serving the maintained opportunity.

## Database contract

The data contract separates semantic type from physical representation and
records identity profiles, numeric profiles, vocabularies, units, digests,
tenant isolation, write policy, relational constraints, compatibility, and
invalidation triggers.

The refactor ledger remains direct:

```text
located schema element
  -> current primitive and material effect
  -> target representation
  -> migration identifier
  -> compatibility and recovery notes
```

Flyway supplies migration ordering, checksums, schema history, locking, and
execution. Timestamp-based versions reduce collisions across parallel branches;
`outOfOrder` remains an environment-level Flyway choice backed by CI validation.
Expand-and-contract changes provide application compatibility across releases.

## Cross-service event delivery

The advisory integration pattern is a thin transactional outbox:

```text
domain transaction + event envelope
  -> outbox table
  -> Debezium or selected CDC platform
  -> idempotent consumer
  -> observable delivery outcome
```

The envelope carries event identity, aggregate identity and version, schema
version, occurrence time, and trace context. The selected broker and CDC
platform own delivery mechanics, retry, and operational recovery.

## Machine Nodes

Machine Nodes give collaborators a small orientation index: repository purpose,
schema release, navigation, current work, next work, later possibilities, and
invalidation conditions. `runtime_effect: none` makes their documentary function
explicit. Application behavior and organizational decisions remain in their
established systems.

## Historical material

Earlier collaboration explored bounded callers, approvals, acceptance records,
receipt closure, release manifests, and cross-record control planes. Those files
remain useful as design history. The active validation set excludes them, and
new implementation work starts from the maintained surface above.

## Repository safety

Examples use synthetic identifiers and placeholder digests. Credentials,
regulated records, personal data, and tenant evidence belong in approved stores.
The repository scan reports secret-shaped values through redacted metadata.
