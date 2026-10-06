# Historical release receipts

## Purpose

This directory preserves an observed promotion receipt after a later release
cycle becomes the active root record.

## Authority

Each filename uses an immutable release tag, and each JSON document validates
against
[`../schemas/promotion-receipt.schema.json`](../schemas/promotion-receipt.schema.json).
The validator binds the file's exact LF-terminated bytes to its repository-owned
SHA-256 identity, preserving the observed tag, commit, archive digest, and
evidence posture.

[`../promotion-receipt.json`](../promotion-receipt.json) owns the active
promotion cycle for the branch being read. A historical receipt establishes
only the release coordinate it names; current release posture remains with the
root orientation set and [`../STATUS.md`](../STATUS.md).

## Use

- [`governance-v2.1.0.json`](governance-v2.1.0.json) records the observed tag
  object, accepted commit, reproducible Git archive digest, and evidence
  posture for Governance 2.1.0.

The later Governance 2.2.0 observation remains the active root promotion
receipt on the `develop` evidence line. It becomes a historical file here when
a successor promotion cycle takes ownership of the root record.

## Verify

From the repository root, validate historical membership, exact bytes, and
schema agreement:

```bash
python3 tools/validate_governance.py
```

At a commit whose root promotion receipt is `release_observed`, verify the live
Git coordinate as well:

```bash
python3 tools/validate_governance.py --verify-release-coordinate
```

The first command establishes the registered historical receipt identities.
The second establishes tag type, tag object, accepted subject, archive digest,
subject ancestry, and exact receipt-carrier bytes for the active observed
release. Signature trust and hosted delivery retain their named evidence
owners.

## Next route

- Read [`../promotion-receipt.json`](../promotion-receipt.json) for the active
  release cycle on the selected branch.
- Read [`../STATUS.md`](../STATUS.md) for the human-readable posture represented
  by that branch.
- Use
  [`governance-schema-release-lineage`](../.agents/skills/governance-schema-release-lineage/SKILL.md)
  to trace one schema from source through its accepted release and retrieval
  copy.
- Use [`../docs/ADOPTION.md`](../docs/ADOPTION.md) when a receiving repository
  is ready to pin an observed coordinate.

## Return to repository root

[Return to the repository orientation](../README.md).
