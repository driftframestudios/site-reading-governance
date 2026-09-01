# Migration from 2.0.0 to 2.0.1

Schema release `2.0.1` retains the stable `/v2.0/` identifier coordinate and
adds an executable repository-promotion record. Existing domain contracts retain
their behavior.

## Consumer actions

1. Set governance `metadata.schema_version` fields to `2.0.1`.
2. Pin the canonical `governance-v2.0.1` annotated tag, accepted commit, and
   SHA-256 digest of its raw `git archive --format=tar` bytes together.
3. Run the governance, language, secret-shape, and regression proofs locally at
   the candidate coordinate.
4. Install branch rulesets that preserve deletion, non-fast-forward,
   one approving review, CODEOWNER review, last-push approval, review-thread
   resolution, and applicable signature protections with an empty hosted
   required-check set in the **$0** resting state.
5. Resolve every CODEOWNER to an eligible reviewer in the repository's current
   ownership model.

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
