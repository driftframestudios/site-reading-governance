# Language policy assets

## Purpose

This directory carries the versioned executable behavior and reviewed-exception
surfaces for `language-policy-v1.0.0`.

## Authority

[`../docs/NEGATION_AWARE_LANGUAGE.md`](../docs/NEGATION_AWARE_LANGUAGE.md) is
the public language authority. The assets here implement its deterministic,
machine-checkable subset. [`manifest.json`](manifest.json) owns policy identity
and digests, [`corpus-v1.json`](corpus-v1.json) owns reviewed behavior cases,
and [`exemptions.json`](exemptions.json) owns time-bounded local exceptions.

The checker establishes agreement with those declared rules. Paragraph-level
meaning, source fidelity, and author judgment remain with review.

## Use

- [`manifest.json`](manifest.json) pins the canonical policy core and
  qualification corpus by Governance path, downstream projection path, and
  SHA-256 digest. Its closed contract also enumerates rule metadata and
  severity, formats and surface kinds, exit meanings, fingerprint semantics,
  and all-or-nothing exemption application.
- [`corpus-v1.json`](corpus-v1.json) defines exact `should_flag`, `should_pass`,
  `exempt`, and `exemption_invalid` behavior across supported formats.
- [`exemptions.json`](exemptions.json) contains findings that received an exact,
  accountable, time-bounded exception. The current inventory is empty.

The repository-independent implementation is
[`../tools/language_policy_core.py`](../tools/language_policy_core.py);
[`../tools/check_language.py`](../tools/check_language.py) is the Governance
repository wrapper. Both use the Python standard library.

### Exemption lifecycle

An exemption identifies one current finding through
`rule_id + path + fingerprint`. The record also names the accountable owner
role, rationale, review timestamp, and expiry timestamp. Review windows span no
more than 180 days, begin no later than evaluation, and end after review.

Each record matches exactly one current occurrence. An expired,
future-reviewed, structurally invalid, duplicate, multiply matched, or unused
record remains an active policy finding. A fully valid registry can apply its
matched exceptions while every output format retains the corresponding
receipts.

### Change journey

A policy change travels with:

1. a release-coordinate decision;
2. representative positive, boundary, and exemption corpus cases;
3. exact output-contract tests;
4. precision review against the repository;
5. regenerated canonical digests and downstream byte-equality checks; and
6. migration notes when downstream behavior changes.

## Verify

From the repository root, run:

```bash
python3 tools/check_language.py
python3 tools/check_language.py --format sarif
python3 -m unittest tests.test_language_assurance -v
```

These commands establish the declared text, JSON, and SARIF contracts,
fingerprints, corpus behavior, exemption lifecycle, and canonical asset
digests. A contextual prose reading establishes whether a changed passage is
clear and faithful to its source.

## Next route

- Read the semantic guidance in
  [`../docs/NEGATION_AWARE_LANGUAGE.md`](../docs/NEGATION_AWARE_LANGUAGE.md).
- Use
  [`contextual-jargon-scan`](../.agents/skills/contextual-jargon-scan/SKILL.md)
  during a bounded public or cross-repository prose change.
- Use [`../CONTRIBUTING.md`](../CONTRIBUTING.md) when a policy, corpus, or
  exemption change is ready for review.

## Return to repository root

[Return to the repository orientation](../README.md).
