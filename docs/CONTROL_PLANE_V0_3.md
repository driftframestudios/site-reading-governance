# Control Plane Profile v0.3

## Purpose

Control Plane Profile v0.3 translates the Enterprise Human-AI Practitioner
Registry into reusable governance contracts for enterprise implementation,
simulation, evidence, and collaboration. Schema release `2.0.1` is the
machine-readable implementation of this profile.

The profile joins five concerns that are frequently documented in isolation:

1. bounded authority for human, service, workflow, AI, and simulated callers;
2. principal-level Practitioner Probes and claim veracity;
3. flexible coordination and resumable handoff;
4. non-authorizing Machine Node orientation; and
5. executable future-reality closure with explicit evidence boundaries.

## Bounded caller contract spine

A caller requests one released, service-owned operation. The service determines
authority and effects.

```text
bounded caller
  -> typed operation request
  -> scope and budget evaluation
  -> approval when the effect requires it
  -> attributable effect
  -> call receipt
  -> replay or owned recovery
```

The contracts establish:

- workload identity and audience;
- an effect-class authority ceiling;
- operation allowlists;
- tenant, resource, record, data-class, and environment scope;
- request, time, retry, and payload budgets;
- tool and egress allowlists;
- equal-or-narrower delegation;
- durable idempotency and replay semantics;
- scoped, expiring approval for broad or irreversible effects;
- append-only decision, approval, effect, result, timing, and correlation
  evidence; and
- containment, replacement behavior, recovery ownership, and verification.

Retrieved content, tool descriptions, repository text, and vendor payloads enter
the boundary as data. Released policy and explicit human direction retain their
declared instruction authority.

## Practitioner Probes and veracity

A Practitioner Probe carries:

- a consequential question and material effect;
- audiences who need the explanation;
- proficiency levels one through five;
- a technical core and review surfaces;
- ordinary, boundary, failure, recovery, and falsifier scenarios;
- linked veracity records;
- instruction yield; and
- `TARGET`, `CONTRAST`, and `GUARD` comment markers.

The proficiency ladder moves from naming the surface, through mechanism and
realistic use, into edge handling, repair, testing, review, and handoff.

Claims carry one status:

- `verified`
- `source_supported`
- `source_specific`
- `draft_probe`
- `local_measurement_needed`
- `correction_needed`
- `hold_for_resilience_pass`

Each claim also records its technology and version band, evidence provenance,
verification method, limitations, review date, recheck triggers, and settlement
status.

## Coordination Horizon

The Coordination Horizon is intentionally generic. It supports any number of
sequenced work items and any collaboration cadence. Each item records:

- a team-selected horizon label;
- active, ready, waiting, settling, or complete state;
- desired state;
- entry and completion evidence;
- owner role; and
- dependencies.

The horizon also records current items, retained effects, consequential
questions, recent decisions, the next safe action, and a verifiable re-entry
capsule.

## Machine Node and first receipt

A Machine Node provides stable orientation:

- canonical identity and repository role;
- control-plane and schema releases;
- orientation-only authority;
- current Coordination Horizon;
- pinned contracts;
- campaigns and marking schema versions;
- seed lineage separated from current provenance;
- first-receipt identifier;
- receipt posture and invalidation conditions;
- downstream consumers; and
- source instruction boundaries.

The first receipt gives each entering collaborator a compact view of contract
state, evidence posture, coordination, source permissions, and handoff. Both
surfaces inform work. Runtime identity, released policy, bounded operations, and
accountable approvals authorize effects.

## Future-reality receipt closure

The simulated closure contract selects a future version of reality and binds:

- a future date and narrative;
- assumptions and immutable source coordinates;
- modeled Scientific, Quality, Regulatory, security, operational, and vendor
  roles;
- exactly four substantive receipt families;
- scenarios, tests, environments, artifacts, and executable reproduction
  commands;
- limitations and divergence triggers; and
- an aggregate result.

The four families are:

1. configured vendor environments;
2. representative migration and restore rehearsals;
3. production security and observability; and
4. accountable Scientific, Quality, and Regulatory acceptance.

A complete manifest states:

```json
{
  "evidence_mode": "simulated",
  "closure_status": "closed_in_simulation",
  "environment_observed_closure": "separate_unasserted_state",
  "production_authorization_effect": "none"
}
```

This is a full closure inside the selected future reality. It requires modeled
roles rather than named organizational people. A separately observed
environment can later produce its own evidence without changing the meaning or
completion of the simulated closure.

## Named probabilities

Every decision probability names:

- the exact event being estimated;
- the beginning and end of its horizon;
- the evaluation event;
- the basis;
- operating conditions;
- recalibration triggers; and
- falsifiers.

The numeric probability therefore remains attached to a reviewable proposition
rather than becoming an unqualified confidence score.

## Adoption sequence

1. Pin governance schema release `2.0.1` and Control Plane Profile `0.3.0`.
2. Add a repository-specific Machine Node and first receipt.
3. Create a Coordination Horizon for the active tranche.
4. Register callers and service-owned operations.
5. Add approval, effect, and call-receipt persistence.
6. Create LIMS and ELN Practitioner Probes with linked veracity records.
7. Execute the four future-reality closure families.
8. Compare regenerated artifacts and record any divergence.
9. Run a settling review and publish successor contracts for material learning.

## Quality gates

- Every schema and mapped example validates.
- Cross-record identifiers and effect classes agree.
- The complete Practitioner Probe proficiency ladder is present.
- Broad-write completion carries approval.
- Every simulated closure artifact is produced by an executable check.
- Scientific, Quality, and Regulatory modeled authority roles are represented.
- Machine orientation retains orientation-only authority.
- Language leads with desired state and pairs hard boundaries with replacement
  behavior.
