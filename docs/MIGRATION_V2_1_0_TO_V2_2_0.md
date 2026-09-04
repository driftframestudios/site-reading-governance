# Migration from 2.1.0 to 2.2.0

Governance `2.2.0` adds retrieval formats for the promotion-receipt family while
JSON Schema remains the machine-validation authority. Stable schema identifiers
stay in the `/v2.0/` family, and Control Plane Profile `0.3.0` keeps its existing
meaning. A consumer can continue using the accepted 2.1.0 coordinate until its
own review selects the observed 2.2.0 release.

## Added projection family

The versioned `promotion-receipt/v1.0.0` family provides:

- a generated YAML 1.2 semantic twin whose parsed data model equals the JSON
  Schema source;
- an authored, query-only GraphQL SDL for bounded inspection; and
- an exact coverage ledger that classifies every reachable JSON Schema
  constraint as directly mapped, represented by an authored directive,
  retained in JSON Schema, or outside the bounded interface.

The GraphQL projection carries fields, enums, reusable types, list shape, and
nullability that GraphQL can express. String grammar, numeric and length ranges,
uniqueness, object closure, required-but-nullable presence, unions, and
cross-field conditions continue to be enforced by JSON Schema. The binding
proof checks enum values, referenced source types, primitive and list shapes,
required-field nullability, and the complete authored field inventory.

## Consumer actions

1. Keep `governance-v2.1.0` as the accepted coordinate during candidate review.
2. Rehearse representative governed records against the 2.2.0 candidate. When
   a record selects this release, set `metadata.schema_version` to `2.2.0`. A
   Machine Node also sets `schema_release` and every campaign
   `marking_schema_version` to `2.2.0`.
   Accepted 2.1.0 Machine Nodes remain valid under the 2.2.0 schema; these
   marker updates record deliberate adoption of the new release rather than a
   prerequisite for continued validation.
3. Run the dependency-free JSON validator for ordinary downstream contract
   validation:

   ```bash
   python3 tools/validate_governance.py \
     --schema schemas/receipt.schema.json \
     --document path/to/receipt.json
   ```

4. Install `requirements-projections.txt` with hash verification when the full
   repository proof, projection proof, or Governance Pages build is part of the
   receiving work. Then run `make check`.
5. After release observation, bind the annotated `governance-v2.2.0` tag, its
   tag object, accepted commit, and SHA-256 digest of the raw
   `git archive --format=tar` bytes together.
6. Retrieve YAML, GraphQL, or coverage bytes from the version-bearing Pages
   path only after the publication receiver verifies the accepted-source
   artifact. Keep the JSON Schema source coordinate beside any projection used
   for interpretation.

Consumers using only JSON Schema gain the 2.2.0 release metadata and retain the
standard-library validation path. Consumers adopting a projection add that
format through a separate reviewed integration so its parser behavior and
intended use remain visible.

## Release and publication sequence

The tagged release tree records `promotion_state: candidate_ready`, planned
evidence, specified assurance, a null `release_coordinate`, and the open `-003`
promotion receipt that existed at acceptance. This later evidence carrier
records the observed coordinate after the following release sequence:

1. run the complete candidate proof and downstream contract rehearsal;
2. merge the approved `release/2.2.0` branch into `main`;
3. create the signed annotated `governance-v2.2.0` tag on that merge commit;
4. reproduce the tagged commit's raw Git archive SHA-256 digest;
5. merge the tagged release forward into `develop`;
6. record the tag object, accepted commit, archive digest, proof locators, and
   receipt-carrier ancestry on a later evidence branch;
7. run `python3 tools/validate_governance.py --verify-release-coordinate` from
   that evidence carrier; and
8. build Governance Pages twice from the clean accepted source, compare every
   byte, verify the artifact, run the generated-artifact secret-shape scan, and
   hand the inspected output to the publication receiver.

The observed Governance 2.1.0 receipt remains in
`release-receipts/governance-v2.1.0.json`. The root promotion receipt describes
the observed 2.2.0 coordinate, and the current horizon routes the verified
artifact to its Pages publication receiver.

## Recovery and compatibility

A receiving repository can return to its accepted 2.1.0 pin while a 2.2.0
integration is revised. Its existing JSON documents retain their 2.1.0 shape
and authority. Projection clients can return to JSON Schema retrieval and use
the coverage ledger to locate the constraint whose interpretation needs review.

The projection family remains a candidate interface in this release. Material
use, compatibility observations, and a later reviewed release decision can
advance that standing without changing the authority of the JSON Schema.
