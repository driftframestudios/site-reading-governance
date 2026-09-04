---
name: repository-reentry
description: Reconstructs current Site Reading Governance truth across source, branch state, root orientation records, release evidence, Pages, and live collaboration. Applies when work resumes, records disagree, or a schema, language, release, or publication task needs an exact starting point.
source_band: public_possible
skill_version: 0.1.0
upstream_repository: driftframestudios/human-ai-systems-exemplars
upstream_path: .agents/skills/repository-reentry/SKILL.md
upstream_revision: 0c023343e46cd9b1333a63c2d509787352fbad14
upstream_blob_sha1: ac2c3732826c515b236598af10e0a204dbe14ace
upstream_sha256: c60bb1bac3a993c78d94b1d05aaa7a97761b99275fc9acdc8285acba6f688f02
adaptation_relation: repository_local_derivative
---

# Governance repository re-entry

## Contract

- **What:** A repository-local method for recovering settled, current, open,
  and next Governance state.
- **When:** Work resumes after a handoff, a branch or pull request changes, or
  source, orientation, release, and publication records appear to disagree.
- **Boundaries:** Runnable source and validators define current behavior.
  Accepted Git objects and promotion evidence define release standing. Root
  orientation records support re-entry, and Pages remains a derived retrieval
  surface. Re-entry observes these roles without granting change authority or
  treating a prior summary as current source.
- **Result:** One authoritative source path, one live collaboration surface,
  the material difference among records, and one bounded next move.

## Rules

### Rule: Current source and accepted release answer different questions

Read the working branch to establish current behavior. Read the promotion
receipt, accepted tag, commit, tree, and archive digest to establish released
standing. A later `develop` change can be current integration work while the
accepted `main` release remains the public contract.

### Rule: The four root records form one re-entry surface

Use `machine-node.json` for repository role and authority posture,
`first-receipt.json` for compact state and handoff,
`coordination-horizon.json` for the current work item and next evidence-bearing
move, and `promotion-receipt.json` for release status. Name any stale carrier
instead of silently blending its earlier state into the current account.

### Rule: Meaning, structure, execution, and retrieval remain distinct

`GOVERNANCE.md` and the focused guide explain meaning and decision rights.
Tracked schemas define machine-checkable structure. The validator and tests
establish executable agreement. Governance Pages copies accepted public-ready
bytes for retrieval. A signal in one role establishes only that role.

### Rule: Branch topology remains visible

Ordinary work begins from `develop`. A release branch assembles a named
candidate for `main`; an accepted hotfix begins from `main` and returns forward
to `develop`. Read the live pull request before treating a local branch name as
the receiving route.

### Rule: Existing work retains its owner

Inspect the worktree before editing. Preserve unrelated changes, and route an
overlap to its current owner when the files cannot be changed independently.

## Operating sequence

1. **Recover Git state:** Run `git status --short --branch`, refresh the
   relevant remote references, and inspect recent history for `main`,
   `develop`, and the active branch.
2. **Read orientation:** Read `README.md`, `AGENTS.md`, `GOVERNANCE.md`,
   `BRANCHING.md`, and the four root orientation records.
3. **Resolve the live receiver:** Read the related Issue or pull request when
   its status, review, or ownership affects continuation.
4. **Inspect the material owner:** Read the exact schema, guide, example,
   validator, workflow, Pages builder, or release record that owns the behavior
   in question.
5. **State the difference:** Separate settled release state, current source,
   open evidence, and the next receiver. Name any record whose language trails
   the accepted behavior.
6. **Choose one move:** Select the smallest source-owned action and the exact
   check that can establish its result.

## Output shape

```text
Current branch and worktree:
Accepted release coordinate:
Current source owner:
Live collaboration surface:
Settled:
Current:
Open:
Stale record, if any:
Next move and verification:
```

## Representative scenario

### Scenario: A release is accepted while a handoff still describes a candidate

Given the annotated Governance tag and observed promotion receipt identify one
accepted release subject<br>
And a root handoff still describes promotion as pending<br>
When repository state is reconstructed<br>
Then the accepted Git and receipt evidence establishes release standing<br>
And current runnable source establishes behavior<br>
And the stale handoff receives one bounded orientation update without changing
the signed release

## Adaptation lineage

This repository-local derivative narrows repository re-entry to Governance's
four root records, schema and language authority, release evidence, and Pages
retrieval boundary. Its upstream revision and content identities preserve the
selected source while this copy remains independently usable.

## Completion

Re-entry completes when another collaborator can identify the current source,
accepted release, live receiver, material difference, and next verified move
without reconstructing the repository's full history.
