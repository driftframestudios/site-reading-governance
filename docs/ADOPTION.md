# Constellation Adoption

## Repository initialization

1. Create the private repository with `main` as its initial branch.
2. Land this package through an administratively reviewed bootstrap change.
3. Create the lean `develop` integration branch from the protected `main`
   baseline.
4. Confirm every configured CODEOWNER resolves to an eligible repository reviewer.
5. Run the local governance validator and regression suite.
6. Review and install the `main` promotion and release-tag ruleset exports.
7. Create and sign canonical release `governance-v2.1.0`.

An approved **100–300 monthly runner-minute** allocation supports the small
pull-request proof. A named receiver can allocate the manual `Governance` proof
by setting `ENABLE_GITHUB_ACTIONS=true`, selecting `confirm_run`, and
dispatching it. Setting the variable to `false` rests the manual path; disabling
Actions in repository settings rests all hosted execution while local proof
continues.

## Downstream contract workflow

A constellation repository can call the pinned reusable workflow after it
chooses to own the remote event and budget:

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
validates the downstream document using the standard-library validator. Both
reusable workflows accept `workflow_call` only. At this revision the five LIMS
repositories contain zero caller workflows, so these remain dormant contract
surfaces. A future caller pins the governance commit and owns its trigger,
Actions setting, permissions, secret, inputs, and receipt interpretation.

## Release coordinate

Each consumer records:

```json
{
  "tag": "governance-v2.1.0",
  "commit_oid": "0123456789abcdef0123456789abcdef01234567",
  "archive_format": "git-tar",
  "archive_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

The annotated tag supports human navigation and object-level verification. The
accepted commit and digest of its raw Git tar archive support exact
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
- confirmation that the `main` branch ruleset carries the reviewed promotion
  protections and its current `required_status_checks` posture;
- confirmation that `develop` remains the lean integration branch;
- CODEOWNER resolution and eligible-reviewer evidence;
- signed release tag;
- reviewer and accountable governance steward.

The lightweight pull-request context first accumulates its observed name,
runner-minute range, and useful evidence. A later required-check change receives
its own activation receipt: stable context name, caller, funded execution path,
branch-policy effect, and return procedure. Its promotion record pairs every
required hosted context with that reviewed receipt.
