# Migration from 2.0.0 to 2.0.1

Schema release `2.0.1` retains the stable `/v2.0/` identifier coordinate and
adds an executable repository-promotion record. Existing domain contracts retain
their behavior.

## Consumer actions

1. Set governance `metadata.schema_version` fields to `2.0.1`.
2. Pin the canonical `governance-v2.0.1` tag, promoted commit, and content
   digest together.
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

Candidate records retain zero commit and digest placeholders,
`promotion_state: candidate_pending`, and an open promotion receipt. After the
protected merge and signed tag:

1. replace Machine Node provenance with the canonical tag, commit, and digest;
2. set the Machine Node lifecycle to `reference_ready` or `active`;
3. populate `promotion-receipt.json.release_coordinate` with the local proof
   receipt, explicit hosted-context list, ruleset, CODEOWNER, tag, commit,
   digest, and timestamp evidence;
4. set the promotion state to `released` with observed evidence;
5. close the promotion receipt in the Machine Node and first receipt; and
6. mark promotion work complete in the Coordination Horizon.

The validator accepts either the coherent candidate state or the coherent
released state and rejects mixed transitions.

An empty `hosted_check_contexts` list records the local-first resting state. A
non-empty list pairs with `hosted_automation_receipt`, which identifies the
separately reviewed caller, funded execution path, and recovery route.
