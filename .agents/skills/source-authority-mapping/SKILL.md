---
name: source-authority-mapping
description: Traces one Governance claim, rule, schema family, example, release record, or public projection through its meaning, structural contract, executable checks, accepted coordinate, delivery route, and downstream use. Applies when those authority roles could be mistaken for one another.
source_band: public_possible
skill_version: 0.1.0
upstream_repository: driftframestudios/human-ai-systems-exemplars
upstream_path: .agents/skills/source-authority-mapping/SKILL.md
upstream_revision: 0c023343e46cd9b1333a63c2d509787352fbad14
upstream_blob_sha1: 112830e9b70540b0bc9a8535ab77c7a04c1a5926
upstream_sha256: 1420eaee7f6d58805c29eaff23644d4982fdf1f12d2f6ce3cc39c65791939aff
adaptation_relation: repository_local_derivative
---

# Governance source authority mapping

## Contract

- **What:** A repository-local method for tracing one material Governance
  object from the source that defines it to the receiver that can act on it.
- **When:** Meaning, schema structure, example data, validation, release
  acceptance, Pages retrieval, or downstream use could be treated as the same
  authority.
- **Boundaries:** The map records evidenced relations and granted decisions.
  It preserves publication, privacy, license, and attribution boundaries.
  Delivery infrastructure carries accepted material without becoming its
  semantic or structural owner.
- **Result:** A concise lineage map naming the material object, source roles,
  typed relations, exact accepted coordinates, current receiver, evidence
  limit, and event that reopens the map.

## Fit and interaction

Use `governance-schema-release-lineage` when the entire decision concerns one
schema's tracked source, accepted release, and byte-identical Pages copy. Use
this broader map when several object types or authority roles participate, such
as a language rule with its corpus and validator, a root orientation family, or
a schema migration with downstream consumers.

## Rules

### Rule: Begin with one material object and decision

Name the claim, rule, schema family, example, release record, or projection and
the decision its route should make possible. A platform inventory is useful
only when it changes that route.

### Rule: Keep authority roles independent

Distinguish the roles that matter:

- semantic meaning and decision rights;
- tracked structural source;
- executable validator and tests;
- example or fixture ownership;
- release acceptance and immutable coordinate;
- Pages publication and hosted delivery; and
- downstream use and accountable acceptance.

One file or repository can carry several roles. Record each role rather than
collapsing them into a general owner label.

### Rule: Type every decision-changing relation

Use literal relations such as `defines`, `validates`, `exemplifies`, `accepts`,
`projects`, `delivers`, `consumes`, or `supersedes`. A Pages copy projects
tracked bytes; a downstream repository consumes a selected release; neither
relation transfers Governance source authority.

### Rule: Identity and retrieval remain separate

A stable schema identifier can remain constant while a source commit, tag,
Pages path, or domain changes. Record the stable identity, accepted revision,
and current retrieval route as separate facts.

### Rule: Promotion carries exact coordinates

When a receiver adopts governed material, retain the source path or identifier,
accepted tag and commit, digest, relation, version, and migration effect needed
for later reconciliation. A floating branch can support exploration while a
governed comparison uses the accepted coordinate.

### Rule: End at a capable receiver

Name the repository, publication action, or accountable role that can make the
next decision. Preserve what the current evidence establishes and which claim
remains with another observation.

## Operating sequence

1. **Name the object and decision.**
2. **Locate meaning:** Read the governing prose and decision boundary.
3. **Locate structure and execution:** Read the tracked schema or rule, its
   examples, validator, and focused tests.
4. **Resolve release and publication:** Read the promotion receipt and Pages
   manifest when accepted or public standing matters.
5. **Trace typed relations:** Follow only the sources and receivers that change
   the decision.
6. **Select the route:** Keep, correct, adapt, project, defer, or return a
   question to the named steward.
7. **Preserve re-entry:** Record the exact source, accepted coordinate,
   evidence boundary, and condition for renewed reconciliation.

## Output shape

```text
Object and decision:

Role | source and path | exact coordinate | relation | established state

Current receiver:
Evidence boundary:
Next action:
Reopen when:
```

## Representative scenario

### Scenario: A language guide and executable policy travel together

Given a Governance guide explains the intended language posture<br>
And a versioned policy manifest, reviewed corpus, and validator implement the
deterministic subset<br>
When a downstream repository adopts the policy<br>
Then the map records the guide as semantic authority and the executable files
as validation authority<br>
And the accepted release coordinate travels with both roles<br>
And the downstream receiver keeps its own prose decisions and exception review
visible

## Adaptation lineage

This repository-local derivative narrows a shared source-authority method to
Governance meaning, schemas, executable policy, release evidence, Pages, and
downstream use. Its upstream revision and content identities preserve the
selected source while this copy remains independently usable.

## Completion

The map is ready when another collaborator can identify what defines the
material, what validates it, which release accepts it, where it can be
retrieved, who can act next, and which change would reopen reconciliation.
