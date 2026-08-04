# Constellation Adoption

## Repository initialization

1. Create the private repository with `main` as its initial branch.
2. Land this package through an administratively reviewed bootstrap change.
3. Create `develop` from the protected `main` baseline.
4. Confirm every configured CODEOWNER resolves to an eligible repository reviewer.
5. Run `Governance` once and record the emitted status-check context.
6. Review and install the versioned ruleset exports.
7. Create and sign canonical release `governance-v2.0.2`.

## Downstream contract workflow

A constellation repository can call the pinned reusable workflow:

```yaml
jobs:
  receipt-contract:
    uses: driftframestudios/site-reading-governance/.github/workflows/reusable-contract-validation.yml@<governance-commit-sha>
    with:
      governance_repository: driftframestudios/site-reading-governance
      governance_ref: <governance-commit-sha>
      schema_name: receipt.schema.json
      document_path: evidence/receipt.json
    secrets:
      governance_read_token: ${{ secrets.GOVERNANCE_READ_TOKEN }}
```

The fine-grained token carries read access to the governance repository. The
workflow checks out both sources with credential persistence disabled and
validates the downstream document using the standard-library validator.

## Release coordinate

Each consumer records:

```json
{
  "release": "governance-v2.0.2",
  "commit": "0123456789abcdef0123456789abcdef01234567",
  "digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

The release tag supports human navigation. The commit and digest support exact
reproduction.

## Evidence storage

Git stores synthetic fixtures, redacted manifests, and content digests. Approved
evidence storage holds raw vendor payloads, regulated records, security findings,
and signed organizational decisions according to access, retention, and audit
policy.

**PRIVACY BOUNDARY:** regulated or identifying evidence must not enter Git history; the replacement behavior is a redacted manifest in Git and a digest-bound locator to the approved evidence store, and manifest validation verifies the locator and digest.

## Ruleset activation receipt

Capture:

- repository and ruleset IDs;
- exported policy digest;
- installation actor and timestamp;
- active aggregate-rule screenshot or API response;
- emitted status-check context;
- CODEOWNER resolution and eligible-reviewer evidence;
- signed release tag;
- reviewer and accountable governance steward.
