# Status

## Current release posture

| Surface | State | Verification |
| --- | --- | --- |
| Governance model | Reference-ready | Document review and tests |
| Branching model | Reference-ready | Ruleset alignment tests |
| JSON schemas | Reference-ready | Meta-structure and exemplar validation |
| Example corpus | Reference-ready | Every example validates against its declared schema |
| Reusable workflows | Reference-ready | Static contract tests |
| Ruleset exports | Review-ready | Structural and status-context checks |
| Language guidance | Reference-ready | Repository language check |

## Receipt boundary

This repository establishes governance capability. Configured-vendor
qualification, representative migration and restore rehearsals, production
security and observability, and accountable scientific, Quality, and Regulatory
acceptance belong to the delivery constellation. Their schemas and example
records live here; their observed evidence remains bound to the named delivery
environment and accountable organization.

## Promotion path

Release `1.0.0` moves through:

1. repository initialization on `main`;
2. `develop` creation from the baseline;
3. `feature/constellation-foundation` review into `develop`;
4. required governance validation on the release coordinate;
5. `release/1.0.0` review into `main`;
6. `develop` synchronization to the released commit;
7. downstream constellation pinning by commit and Git tree digest.

Ruleset installation, organization-specific CODEOWNER confirmation, and signed
tag publication remain accountable adoption receipts for the hosting
organization.

## Known extension points

- organization-specific CODEOWNER handles;
- organization and repository IDs in ruleset installation tooling;
- organization-specific governed-locator resolver registry;
- retention schedules and jurisdictional overlays;
- artifact attestation when the selected GitHub plan supports it;
- organization-specific scientific, Quality, and Regulatory roles.

## Open governance receipts

- `GOV-RCP-ACCEPT-001` — bind actual accountable acceptance to an immutable
  external authorization record carrying identity assurance, signed time,
  payload digest, and approved-system coordinate.
- `GOV-RCP-DISPOSITION-001` — define the accountable exception disposition for
  a failed or inconclusive receipt before any accepted assurance stage can
  advance.

These receipts preserve the current schema boundary explicitly. Their successor
contracts will include examples, negative fixtures, migration guidance, and
accountable Quality and security review.
