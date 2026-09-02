---
name: governance-schema-release-lineage
description: Traces one Site Reading Governance schema from tracked source through an accepted release coordinate to its byte-identical Pages retrieval copy. Applies when schema meaning, release identity, public projection, or downstream use needs a verifiable source and receiver.
source_band: public_ready
skill_version: 0.1.1
lineage_key: lims-src-006
adaptation_relation: repository_local_derivative
---

# Governance schema release lineage

## Contract

- **What:** A repository-local method for following one governance schema from
  its tracked definition through an accepted release coordinate to an exact
  public retrieval copy and a named downstream receiver.
- **When:** A schema path, stable identifier, release tag, source revision,
  Pages file, or consumer binding could be mistaken for another authority or
  version.
- **Boundaries:** Tracked governance source retains meaning and structural
  authority. The protected release path establishes the accepted coordinate.
  The Pages manifest establishes projection identity and completeness. Hosted
  delivery, domain configuration, material suitability, and accountable
  acceptance retain their own owners and evidence.
- **Result:** A compact map naming the schema source, stable identifier,
  accepted release coordinate, byte-identical retrieval path, current receiver,
  evidence boundary, and event that would reopen the map.

## Rules

### Rule: Begin with one schema and one decision

Name the exact `schemas/*.schema.json` path, its `$id`, and the decision that
becomes possible after its lineage is clear. Use `schemas/README.md` to confirm
the schema's ordinary-language job.

### Rule: Keep meaning with tracked source

The schema bytes define machine-checkable structure. `GOVERNANCE.md` explains
meaning, decision rights, evidence stages, review, and recovery. A passing
schema validation establishes structural agreement with those selected bytes;
material suitability and accountable acceptance receive their own evidence.

### Rule: Carry the accepted release coordinate

Read `promotion-receipt.json` and the root orientation records. An observed
release map carries the annotated tag, tag object, accepted commit, archive
format, archive SHA-256 digest, later receipt carrier, and relation to the
schema source. Candidate placeholders remain explicit until protected
promotion supplies observed values.

### Rule: Prove the retrieval copy from both sides

Use the Pages manifest record for the selected schema. Confirm its source path,
output path, stable identifier, full-SHA source URL, byte length, and SHA-256
digest, then compare the tracked source bytes with the published file. The
matching bytes and digest establish content identity. They leave semantic
quality and fitness for a particular use with their fitting review.

### Rule: Keep delivery separate from schema authority

The generated artifact records its producing revision, relative retrieval
paths, optional canonical origin, and closed file inventory. GitHub Pages
settings, a custom domain, DNS, and hosted response behavior describe delivery.
They carry the schema without redefining its meaning or release status.

### Rule: End at the next capable receiver

Name the consumer that can act: a program release, implementation, simulation,
comparison, publication receiver, or accountable acceptance role. Preserve the
schema identifier, accepted commit, release tag, governed digest, evidence mode,
and relation that the receiver needs.

## Operating sequence

1. **Name the object:** Record the schema path, `$id`, intended decision, and
   current branch or accepted source revision.
2. **Locate authority:** Read the schema, its catalog entry, and the governance
   passage that explains its use and decision boundary.
3. **Resolve release standing:** Read the promotion receipt and orientation
   records. Run release-coordinate verification when the receipt records an
   observed release.
4. **Locate the projection:** Find the schema's manifest record and versioned
   Pages output path at the same full source revision.
5. **Compare identity:** Compare source and output bytes, byte length, stable
   identifier, and SHA-256 digest. Record what each signal establishes.
6. **Hand to the receiver:** State the relation, evidence mode, receiving
   decision, next action, and event that requires another lineage pass.

## Output shape

```text
Schema and decision:

Role | repository and path | exact coordinate | relation | established state

Current receiver:
Evidence boundary:
Next action:
Reopen when:
```

## Representative scenario

### Scenario: An accepted schema reaches a downstream validation record

Given one schema in the current accepted Governance release retains its stable
`/v2.0/` identifier<br>
And an observed promotion receipt binds the annotated release tag, accepted
commit, and reproducible archive digest<br>
When Governance Pages copies that schema to its versioned retrieval path and
records the same source path, full revision, bytes, identifier, and SHA-256<br>
Then the map records `defines`, `accepts`, and `projects` as separate relations<br>
And the downstream record pins the accepted coordinate and selected schema<br>
And a change to the tracked schema, release coordinate, projection bytes, or
consumer requirement reopens the map from the changed source

## Adaptation lineage

This repository-local derivative narrows a shared method for tracing source and
authority to one Governance schema, the accepted promotion receipt, its
byte-identical Pages retrieval copy, and the downstream receiver. Public
lineage key `lims-src-006` identifies the selected source within its authorized
resolver. The public guide carries the relation, purpose, and evidence standing
while exact gated lineage stays recoverable through that resolver. Future
revisions preserve this lineage pair or record a new relation.

## Completion

The map is ready when another collaborator can identify the source that defines
the schema, verify the accepted release coordinate, compare the retrieval copy
byte for byte, distinguish publication from schema meaning, name the receiver
that can act, and return to the exact change that would reopen the map.
