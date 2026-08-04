# Migration from 2.0.0 to 2.0.1

Schema release `2.0.1` retains the stable `/v2.0/` identifier coordinate and
adds an executable repository-promotion record. Existing domain contracts retain
their behavior.

## Consumer actions

1. Set governance `metadata.schema_version` fields to `2.0.1`.
2. Pin the canonical `governance-v2.0.1` tag, promoted commit, and content
   digest together.
3. Pass a full 40-hex governance commit to reusable contract validation.
4. Require both `branch-policy` and the substantive validation context in branch
   rulesets.
5. Resolve every CODEOWNER to an eligible reviewer in the repository's current
   ownership model.

## Promotion lifecycle

Candidate records retain zero commit and digest placeholders,
`promotion_state: candidate_pending`, and an open promotion receipt. After the
protected merge and signed tag:

1. replace Machine Node provenance with the canonical tag, commit, and digest;
2. set the Machine Node lifecycle to `reference_ready` or `active`;
3. populate `promotion-receipt.json.release_coordinate` with observed check,
   ruleset, CODEOWNER, tag, commit, digest, and timestamp evidence;
4. set the promotion state to `released` with observed evidence;
5. close the promotion receipt in the Machine Node and first receipt; and
6. mark promotion work complete in the Coordination Horizon.

The validator accepts either the coherent candidate state or the coherent
released state and rejects mixed transitions.
