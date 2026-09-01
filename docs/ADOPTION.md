# Constellation Adoption

## Repository initialization

1. Create the private repository with `main` as its initial branch.
2. Land this package through an administratively reviewed bootstrap change.
3. Create `develop` from the protected `main` baseline.
4. Confirm every configured CODEOWNER resolves to an eligible repository reviewer.
5. Run the local governance validator and regression suite.
6. Review and install the versioned ruleset exports with an empty hosted-check
   resting state.
7. Create and sign canonical release `governance-v2.0.1`.

GitHub Actions rests disabled in repository settings at a **$0** budget. A named
human can allocate the manual `Governance` proof by enabling Actions, setting
`ENABLE_GITHUB_ACTIONS=true`, selecting `confirm_run`, and dispatching it. The
named human sets `ENABLE_GITHUB_ACTIONS=false` and disables Actions in
repository settings after the receipt is read.

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
  "tag": "governance-v2.0.1",
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
- confirmation that branch rulesets contain no `required_status_checks` rule in
  the $0 resting state;
- CODEOWNER resolution and eligible-reviewer evidence;
- signed release tag;
- reviewer and accountable governance steward.

A later hosted context enters through its own activation receipt: stable
context name, caller or manual workflow, funded execution path, branch-policy
effect, and return procedure. Its promotion record pairs every hosted context
with that reviewed receipt.
