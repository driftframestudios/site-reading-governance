# Language Policy Assets

This directory carries the executable behavior and reviewed-exception surfaces
for `language-policy-v1.0.0`.

## Assets

- `manifest.json` pins the canonical policy core and qualification corpus by
  governance path, downstream projection path, and SHA-256 digest. Its closed
  contract also enumerates rule metadata and severity, formats and surface
  kinds, exit meanings, fingerprint semantics, and all-or-nothing exemption
  application.
- `corpus-v1.json` defines exact `should_flag`, `should_pass`, `exempt`, and
  `exemption_invalid` behavior across supported formats.
- `exemptions.json` contains repository findings that received an exact,
  accountable, time-bounded exception. The candidate inventory is empty.

The repository-independent implementation is
`tools/language_policy_core.py`; `tools/check_language.py` is the governance
repository wrapper. Both use only the Python standard library.
`tests/test_language_assurance.py` executes the entire corpus and verifies
parsing, exemption lifecycle, stable fingerprints, compatibility APIs,
canonical asset digests, and text/JSON/SARIF output contracts.

## Exemption review

An exemption identifies one current finding through the tuple
`rule_id + path + fingerprint`. The record also names the accountable owner
role, rationale, review timestamp, and expiry timestamp. Review windows span no
more than 180 days, begin no later than evaluation, and end after review.

Each record matches exactly one current occurrence. The checker reports an
expired, future-reviewed, structurally invalid, duplicate, multiply matched,
or unused record as an active policy finding. Any such finding keeps the whole
registry from suppressing results, while successful runs retain applied
exemption receipts in every output format.

## Change protocol

A policy change travels with:

1. a release-coordinate decision;
2. representative positive, negative, and exemption corpus cases;
3. exact output-contract tests;
4. precision review against the repository;
5. regenerated canonical digests and downstream byte-equality checks; and
6. migration notes when downstream behavior changes.
