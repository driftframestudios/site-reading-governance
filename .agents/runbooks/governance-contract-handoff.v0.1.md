---
title: Governance contract handoff
version: 0.1.0
status: working
audience: Governance maintainers and receiving repository collaborators
source_band: public_possible
task_type: contract_handoff
---
# Governance contract handoff 0.1

Return one reviewed source coordinate and a scope-explicit check result to the
named receiver. Completion keeps source acceptance, package adoption, and
public delivery independently identifiable.

## Entry and authority

Receive the exact source revision, profile schema, mapped example, compatibility
map, and receiving task. Governance owns the companion; upstream packages retain
domain semantics. The human release receiver owns publication and promotion.

The [companion guide](../../docs/ADMINISTRATIVE_ASSURANCE.md) and
[`requirements-assurance.txt`](../../requirements-assurance.txt) define the
receiving profile. Enter with an explicit grant for local source and checks.
An unavailable dependency or unknown source coordinate returns `friction` to
its owner; existing accepted records remain available.

## Checks and exercise

1. Run schema/catalog/example checks and the focused companion tests.
2. In the optional pinned environment, exercise the complete pack/study/report,
   changed source and oracle, mixed identity, incomplete input, and correction.
3. Run the repository's language and secret-shape checks on the proposed source.
4. Obtain independent review of the receiving boundary and recovery behavior.
5. Return one PR containing normalized results, coverage, compatibility standing,
   and the next receiving Issue. Detailed local diagnostics retain their local owner.

### Bounded local command route

From the repository root in the isolated profile environment:

```sh
python -m unittest discover -s tests -p 'test_assurance_*.py' -v
python tools/validate_governance.py
python tools/check_language.py
python tools/scan_secret_shapes.py --root .
```

`test_assurance_exercises.py` supplies the decision/override/recourse,
population-control/small-cell/omission, and policy/intended-use exercises. Its
route test also checks metadata and local links. The existing companion and
upstream tests retain digest, source/oracle, eligibility, and prior-record
counterexamples. Use the scanner's `scan_text` and `report` functions to require
a fresh, process-only synthetic provider-shaped canary to produce a redacted
finding before interpreting the owning-root tree scan. Canary failure holds
the return. The tree scan's textual working scope stays distinct from Git
history and hosted material.

The public-safe handback contains the source revision, selected commands,
normalized counts, evidence boundary, and next receiver. Local source overlays
are named as such; exact installed-package acceptance remains a separate check.
A stacked source review returns to its named base branch. Merge, tag, hosted
publication, and external model execution wait for their explicit human grants.

## Recovery and stopping event

A typed receiving error returns to its named contract owner. Preserve accepted
source and previous evidence while the smallest affected check is renewed.
Stop at a reviewed source-level result with one exact next action.

## Handback and acceptance event

Governance #38 receives the exercised assurance slice; #49 receives the
composition-versus-execution boundary. The runbook exercise remains distinct
from broader parent acceptance. A tagged public carrier and hosted publication
follow their existing explicit release decisions.
