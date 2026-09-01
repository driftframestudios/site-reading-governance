# Migration from 2.0.0 to 2.1.0

Schema release `2.1.0` retains the stable `/v2.0/` identifier family and adds
backward-compatible contract capabilities. Existing 2.0.0 contract files keep
their identifiers and document behavior. Consumers can adopt the new families
when their work needs them.

## Added contract families

- `promotion-receipt` separates a release candidate from the later observation
  of its accepted tag, commit, and archive bytes.
- `language-control` binds a desired state, protected boundary, replacement
  behavior, verification, and accountable ownership.
- `data-contract`, `database-refactor-finding`, `database-migration-plan`,
  `database-migration-receipt`, `data-reconciliation`, and
  `database-release-manifest` form an additive database-change evidence chain.

The release also adds deterministic language assurance, bounded pull-request
automation, and a reproducible Governance Pages builder. These repository
capabilities support the contracts without changing an existing 2.0.0
document's structural meaning.

## Consumer actions

1. Set `metadata.schema_version` to `2.1.0` when selecting this release.
2. Pin the canonical `governance-v2.1.0` annotated tag, accepted commit, and
   SHA-256 digest of its raw `git archive --format=tar` bytes together.
3. Run the governance, language, secret-shape, and regression proofs locally at
   the candidate coordinate.
4. Install the `main` promotion ruleset and release-tag ruleset. Preserve
   deletion, non-fast-forward, one approving review, CODEOWNER review,
   last-push approval, review-thread resolution, and applicable signature
   protections on `main`, while `develop` remains the lean integration branch.
   Keep the hosted required-check list distinct from the observed lightweight
   pull-request proof until a separate review establishes a stable context and
   recovery route.
5. Resolve every CODEOWNER to an eligible reviewer in the repository's current
   ownership model.

Consumers that use only the 2.0.0 contract set can keep their existing document
shape while pinning 2.1.0. A consumer adopting one of the added families should
add the corresponding record and its materially related evidence together.

A future reusable-workflow caller supplies a full 40-hex governance commit and
owns its event, Actions setting, budget, permissions, secrets, and receipt
interpretation through a separate reviewed activation.

## Promotion lifecycle

The release tree carries `promotion_state: candidate_ready`, a null
`release_coordinate`, and an open promotion receipt. After the protected merge
and signed annotated tag:

1. resolve the annotated tag object and its accepted commit;
2. compute the SHA-256 digest of `git archive --format=tar <accepted-commit>`;
3. merge the tagged release forward into `develop`;
4. create a later evidence commit that populates
   `promotion-receipt.json.release_coordinate` with the Git object format, tag
   object, accepted commit, archive format and digest, timestamp, local proof,
   explicit hosted posture, ruleset, CODEOWNER, and tag-signature locators;
5. set the promotion state to `release_observed` with observed evidence;
6. replace Machine Node provenance with the canonical tag, accepted commit,
   and archive digest, then set its lifecycle to `reference_ready` or `active`;
7. close the promotion receipt in the Machine Node and first receipt;
8. mark promotion work complete in the Coordination Horizon; and
9. run `python3 tools/validate_governance.py --verify-release-coordinate` from
   the evidence commit.

The validator accepts either the coherent candidate state or the coherent
observed-release state. Git-backed verification establishes that the annotated
tag resolves to the recorded source, the archive digest reproduces, the source
is an ancestor of the later receipt carrier, and the carrier contains the
selected receipt bytes.

This local observation validates Git object relationships and archive bytes.
The `tag_signature_receipt` routes cryptographic signature evidence to its
governed owner and remains the release steward's separate verification.

An empty `hosted_check_contexts` list and null `hosted_automation_receipt`
record the local-first resting state. A populated list pairs with a governed
`hosted_automation_receipt`, which identifies the separately reviewed caller,
funded execution path, and recovery route.
