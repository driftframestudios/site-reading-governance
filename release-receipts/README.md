# Historical release receipts

This directory preserves each observed promotion receipt after a later release
candidate becomes the root orientation record. Each filename uses the immutable
release tag, and each JSON document continues to validate against
`schemas/promotion-receipt.schema.json`. The validator also binds every
document's exact LF-terminated bytes to a repository-owned SHA-256 identity, so
its complete observed account remains stable alongside the release archive
digest it carries.

The root [`promotion-receipt.json`](../promotion-receipt.json) describes the
active promotion cycle. A historical receipt establishes only the release
coordinate it names; current release posture remains with the root orientation
records and `STATUS.md`.

## Receipts

- [`governance-v2.1.0.json`](governance-v2.1.0.json) — observed tag object,
  accepted commit, and reproducible Git archive digest for Governance 2.1.0.
